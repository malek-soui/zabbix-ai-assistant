# vm_discovery.ps1 - Outputs full JSON array of all Hyper-V VMs with stats

$tailscaleData = @{}
try {
    $json = tailscale status --json | ConvertFrom-Json
    $json.Peer.PSObject.Properties.Value | ForEach-Object {
        $tailscaleData[$_.HostName] = @{
            IP = $_.TailscaleIPs[0]
            DNSName = $_.DNSName.TrimEnd('.')
        }
    }
} catch {}

$vms = Get-VM

$result = @()

foreach ($vm in $vms) {
    $vmName = $vm.Name

    # Disk info (sum all VHDs per VM)
    $provisionedGB = 0
    $usedGB = 0
    try {
        $vhds = Get-VHD -VMId $vm.VMId -ErrorAction Stop
        foreach ($vhd in $vhds) {
            $provisionedGB += [math]::Round($vhd.Size / 1GB, 2)
            $usedGB += [math]::Round($vhd.FileSize / 1GB, 2)
        }
    } catch {}
# Network throughput via Hyper-V performance counters
    $networkKbps = 0
    try {
        $netAdapter = Get-VMNetworkAdapter -VMName $vmName -ErrorAction Stop | Select-Object -First 1
        if ($netAdapter) {
            $counterPath = "\Hyper-V Virtual Network Adapter(*$vmName*)\Bytes/sec"
            $counterData = Get-Counter -Counter $counterPath -ErrorAction SilentlyContinue
            if ($counterData) {
                $bytesPerSec = ($counterData.CounterSamples | Measure-Object -Property CookedValue -Sum).Sum
                $networkKbps = [math]::Round(($bytesPerSec * 8) / 1KB, 2)
            }
        }
    } catch {}

    # Disk I/O via Hyper-V performance counters
    $diskIops = 0
    try {
        $counterPath = "\Hyper-V Virtual Storage Device(*$vmName*)\Read Operations/Sec"
        $counterData = Get-Counter -Counter $counterPath -ErrorAction SilentlyContinue
        if ($counterData) {
            $diskIops = [math]::Round(($counterData.CounterSamples | Measure-Object -Property CookedValue -Sum).Sum, 2)
        }
    } catch {}

    # Guest OS via KVP
    $guestOS = "Unknown"
    try {
        $kvpItems = Get-CimInstance -Namespace root\virtualization\v2 -ClassName Msvm_ComputerSystem -Filter "ElementName='$vmName'" |
            Get-CimAssociatedInstance -ResultClassName Msvm_KvpExchangeComponent |
            Select-Object -ExpandProperty GuestIntrinsicExchangeItems
        foreach ($item in $kvpItems) {
            if ($item -match '<VALUE>OSName</VALUE>') {
                continue
            }
        }
        $xmlItems = [xml[]]($kvpItems | ForEach-Object { "<root>$_</root>" })
        foreach ($x in $xmlItems) {
            $nameNode = $x.root.INSTANCE.PROPERTY | Where-Object { $_.NAME -eq 'Name' }
            if ($nameNode.VALUE -eq 'OSName') {
                $dataNode = $x.root.INSTANCE.PROPERTY | Where-Object { $_.NAME -eq 'Data' }
                $guestOS = $dataNode.VALUE
            }
        }
    } catch {}

    # Tailscale IP / DNS lookup
    $ip = ""
    $dns = ""
    if ($tailscaleData.ContainsKey($vmName)) {
        $ip = $tailscaleData[$vmName].IP
        $dns = $tailscaleData[$vmName].DNSName
    }

    # Memory demand (usage) - handle French comma decimal
    $memDemandRaw = $vm.MemoryDemand
    $memUsageGB = if ($memDemandRaw) { [math]::Round($memDemandRaw / 1GB, 2) } else { 0 }
    $memAssignedGB = [math]::Round($vm.MemoryAssigned / 1GB, 2)
    $memUsagePercent = if ($vm.MemoryAssigned -gt 0) { [math]::Round(($memDemandRaw / $vm.MemoryAssigned) * 100, 2) } else { 0 }

    $result += [PSCustomObject]@{
        state             = $vm.State.ToString()
        name              = $vmName
        status            = $vm.Status
        host              = $env:COMPUTERNAME
        provisioned_space = $provisionedGB
        used_space        = $usedGB
        cpu_usage         = $vm.CPUUsage
        memory_usage_pct  = $memUsagePercent
        memory_usage_gb   = $memUsageGB
        ipv4_address      = $ip
        dns_name          = $dns
        vcpu              = $vm.ProcessorCount
        assigned_memory   = $memAssignedGB
        guest_os          = $guestOS
	network_kbps      = $networkKbps
        disk_iops         = $diskIops
    }
}

$result | ConvertTo-Json -Depth 3 -Compress

# --- Push data to Zabbix via zabbix_sender for each discovered VM ---
$senderExe = "C:\Program Files\Zabbix Agent 2\zabbix_sender.exe"
$zabbixServer = "localhost"
$zabbixPort = "10051"

$pskMap = @{
    "HV-HOST-01" = @{ identity = "PSK_HV-HOST-01"; file = "C:\zabbix-scripts\hv01_psk.txt" }
    "HV-HOST-02" = @{ identity = "PSK_HV-HOST-02"; file = "C:\zabbix-scripts\hv02_psk.txt" }
}

foreach ($vm in $result) {
    $hostName = $vm.name


    $dataLines = @(
        "$hostName vm.name $($vm.name)"
        "$hostName vm.state $($vm.state)"
        "$hostName vm.status $($vm.status)"
        "$hostName vm.host $($vm.host)"
        "$hostName vm.provisioned $($vm.provisioned_space)"
        "$hostName vm.used $($vm.used_space)"
        "$hostName vm.cpu $($vm.cpu_usage)"
        "$hostName vm.mempct $($vm.memory_usage_pct)"
        "$hostName vm.memgb $($vm.memory_usage_gb)"
        "$hostName vm.ip $($vm.ipv4_address)"
        "$hostName vm.dns $($vm.dns_name)"
        "$hostName vm.vcpu $($vm.vcpu)"
        "$hostName vm.assignedmem $($vm.assigned_memory)"
        "$hostName vm.os `"$($vm.guest_os)`""
	"$hostName vm.network $($vm.network_kbps)"
        "$hostName vm.diskio $($vm.disk_iops)"
    )

$tempFile = [System.IO.Path]::GetTempFileName()
    $dataLines | Out-File -FilePath $tempFile -Encoding ASCII

    $psk = $pskMap[$hostName]
    if ($psk) {
        & $senderExe -z $zabbixServer -p $zabbixPort -i $tempFile --tls-connect psk --tls-psk-identity $psk.identity --tls-psk-file $psk.file 2>&1 | Out-Null
    } else {
        & $senderExe -z $zabbixServer -p $zabbixPort -i $tempFile 2>&1 | Out-Null
    }

    Remove-Item $tempFile -Force
}
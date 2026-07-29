INCIDENTS = [
    {
        "id": "INC001",
        "text": "CPU spike on DB_Server during nightly backup window. Resolved by rescheduling backup to run during low-traffic hours."
    },
    {
        "id": "INC002",
        "text": "Memory leak detected on Web_Server after a software update. Fixed by rolling back to the previous application version and reporting the bug to the vendor."
    },
    {
        "id": "INC003",
        "text": "Disk space critically low on Server02 due to accumulated log files. Resolved by enabling automatic log rotation and archiving old logs."
    },
    {
        "id": "INC004",
        "text": "High CPU usage on HV-HOST-01 caused by a runaway process from a stuck scheduled task. Killed the process and fixed the task scheduler configuration."
    },
    {
        "id": "INC005",
        "text": "Network latency spike on VM cluster during peak business hours, traced to insufficient bandwidth allocation. Resolved by increasing the network adapter's bandwidth limit."
    },
    {
        "id": "INC006",
        "text": "VM went into a paused state unexpectedly due to a host storage failure. Resolved by migrating the VM to a healthy host and investigating the storage array."
    },
    {
        "id": "INC007",
        "text": "Zabbix agent stopped responding on HV-HOST-02 after a Windows update reset the firewall rules. Fixed by re-adding the required inbound firewall exceptions."
    },
    {
        "id": "INC008",
        "text": "Memory usage gradually climbing on a VM over several days, consistent with a slow memory leak in a long-running application. Resolved by scheduling a weekly service restart."
    }
]
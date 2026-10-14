# Shadow AI simulation: send browser-like requests to consumer AI sites THROUGH the lab's Squid proxy.
# Squid denies them (403) and logs each attempt; Wazuh raises 100101 per attempt and 100102 after 10 in 10 minutes.
# Run from PowerShell on Windows: .\scripts\simulate_shadow_ai.ps1
param(
    [int]$Count = 12,
    [string]$Proxy = "http://127.0.0.1:3128"
)
$sites = @("https://chatgpt.com", "https://claude.ai", "https://gemini.google.com", "https://chat.deepseek.com")
for ($i = 1; $i -le $Count; $i++) {
    $site = $sites[$i % $sites.Count]
    $code = curl.exe -s -o NUL -w "%{http_code}" -x $Proxy $site
    Write-Output "$i  $site  -> proxy answered $code"
    Start-Sleep -Milliseconds 300
}
Write-Output "Done. Check Wazuh for rules 100101 and 100102, and lab/logs/squid/access.json."

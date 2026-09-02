function Stop-TestServerProcess {
    param(
        [Parameter(Mandatory = $true)]
        [Diagnostics.Process]$Process
    )

    if (-not $Process.HasExited) {
        try {
            # Windows PowerShell 5.1 / .NET Framework udostępnia Kill() bez
            # przeciążenia Kill(Boolean), które pojawiło się w nowszym .NET.
            $Process.Kill()
        }
        catch [InvalidOperationException] {
            # Proces mógł zakończyć się pomiędzy HasExited i Kill(). Tylko ten
            # wyścig jest bezpieczny do zignorowania; inne błędy są propagowane.
            if (-not $Process.HasExited) {
                throw
            }
        }
    }

    # Działa również dla procesu, który zakończył się samodzielnie. Zapewnia,
    # że asynchroniczne strumienie stdout/stderr zostały opróżnione.
    $Process.WaitForExit()
}

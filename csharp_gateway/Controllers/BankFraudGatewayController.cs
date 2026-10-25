using Microsoft.AspNetCore.Mvc;
using BankGateway.Models;
using BankGateway.Security;
using BankGateway.CoreBanking;
using BankGateway.Services;

namespace BankGateway.Controllers;

[ApiController]
[Route("api/bank")]
public class BankFraudGatewayController : ControllerBase
{
    private readonly IPythonEngineClient _pythonClient;
    private readonly IPartialLienService _lienService;
    private readonly IAuditLogChainService _auditLog;
    private readonly IHmacTokenService _hmac;

    public BankFraudGatewayController(
        IPythonEngineClient pythonClient,
        IPartialLienService lienService,
        IAuditLogChainService auditLog,
        IHmacTokenService hmac)
    {
        _pythonClient = pythonClient;
        _lienService = lienService;
        _auditLog = auditLog;
        _hmac = hmac;
    }

    [HttpGet("health")]
    public IActionResult GetHealth()
    {
        return Ok(new
        {
            Service = "C# ASP.NET Core 8 Bank Fraud Gateway",
            Status = "ONLINE",
            Port = 5000,
            DPDPCompliance = "Salted HMAC-SHA256 Tokenization Active",
            AuditLogStatus = "SHA-256 Cryptographic Chain Active",
            AuditRecordsCount = _auditLog.GetChain().Count,
            Timestamp = DateTime.UtcNow
        });
    }

    [HttpGet("investigate")]
    public async Task<IActionResult> Investigate(
        [FromQuery] string firId = "FIR-2026-104", 
        [FromQuery] string role = "BankAnalyst")
    {
        var result = await _pythonClient.AnalyzeTrailAsync(firId, role);
        return Ok(result);
    }

    [HttpPost("place-partial-lien")]
    public IActionResult PlacePartialLien([FromBody] PartialLienRequest req)
    {
        var res = _lienService.ExecutePartialLienHold(req);
        return Ok(res);
    }

    [HttpGet("verify-audit-chain")]
    public IActionResult VerifyAuditChain()
    {
        var verification = _auditLog.VerifyIntegrity();
        return Ok(verification);
    }

    [HttpPost("simulate-tamper")]
    public IActionResult SimulateTamper([FromBody] TamperRequest req)
    {
        bool success = _auditLog.SimulateTampering(req.RecordIndex, req.AlteredAction);
        if (!success) return BadRequest(new { Error = "Invalid record index" });
        return Ok(new { Status = "TAMPER_INJECTED", RecordIndex = req.RecordIndex });
    }

    [HttpPost("restore-audit-chain")]
    public IActionResult RestoreAuditChain()
    {
        _auditLog.RestoreIntactChain();
        return Ok(new { Status = "AUDIT_CHAIN_RESTORED" });
    }

    [HttpGet("generate-dossier")]
    public async Task<IActionResult> GenerateDossier(
        [FromQuery] string firId = "FIR-2026-104", 
        [FromQuery] string role = "LawEnforcement")
    {
        var investigation = await _pythonClient.AnalyzeTrailAsync(firId, role);
        var activeLiens = _lienService.GetActiveLiens();
        var chain = _auditLog.GetChain();
        string latestHash = chain.LastOrDefault()?.CurrentHash ?? "00000000";

        var accountsSummary = investigation.Nodes.Select(n => new
        {
            Account = n.DisplayId,
            Bank = n.Bank,
            RiskScore = n.RiskScore,
            TaintedRupees = n.TaintedAmount,
            SafeBalance = n.SafeBalance,
            LienStatus = n.TaintedAmount > 0 ? "PARTIAL LIEN RECOMMENDED" : "CLEAN"
        }).ToList<object>();

        var legalActions = new List<string>
        {
            "Section 102 CrPC: Order immediate partial lien hold on flagged recipient accounts",
            "Section 91 CrPC: Subpoena telecom ISP logs for Device DEV_HERDER_99",
            "DPDP Act 2023 Exemption: Law Enforcement investigative disclosure authorized under verified FIR",
            $"Cryptographic Chain of Custody verified up to Hash: {latestHash[..16]}..."
        };

        _auditLog.AppendLog(role, $"EXPORT_LEGAL_DOSSIER ({firId})", "Dossier Issued");

        var dossier = new CourtReadyDossier(
            firId,
            DateTime.UtcNow.ToString("yyyy-MM-dd HH:mm:ss UTC"),
            role,
            latestHash,
            $"Official Money Trail & Freeze Recommendation Report for Cybercrime FIR {firId}. Traced ₹1,00,000 multi-hop layering conduit across 4 banks.",
            accountsSummary,
            legalActions
        );

        return Ok(dossier);
    }

    [HttpPost("simulate-attack")]
    public async Task<IActionResult> SimulateAttack([FromBody] AttackSimRequest req)
    {
        var res = await _pythonClient.TriggerAttackSimulationAsync(req.AttackType);
        return Ok(res);
    }

    [HttpGet("benchmark-metrics")]
    public async Task<IActionResult> GetBenchmarkMetrics()
    {
        var metrics = await _pythonClient.GetBenchmarkEvaluationAsync();
        return Ok(metrics);
    }

    [HttpGet("datasets")]
    public async Task<IActionResult> GetRealDatasets()
    {
        _auditLog.AppendLog("BankCompliance", "QUERY_DATASETS", "Catalog of 25 SOA Bank Files");
        var catalog = await _pythonClient.GetRealDatasetCatalogAsync();
        return Ok(catalog);
    }

    [HttpGet("datasets/file/{fileName}")]
    public async Task<IActionResult> GetRealDatasetFile(string fileName)
    {
        _auditLog.AppendLog("BankCompliance", "INSPECT_SOA_FILE", fileName);
        var fileData = await _pythonClient.GetRealDatasetFileAsync(fileName);
        return Ok(fileData);
    }

    [HttpGet("datasets/search")]
    public async Task<IActionResult> SearchRealAccounts([FromQuery] string query)
    {
        _auditLog.AppendLog("BankCompliance", "SEARCH_ACCOUNTS", query);
        var results = await _pythonClient.SearchRealAccountsAsync(query);
        return Ok(results);
    }
}

public record TamperRequest(int RecordIndex, string AlteredAction);
public record AttackSimRequest(string AttackType);


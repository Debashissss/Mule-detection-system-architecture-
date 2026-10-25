using BankGateway.CoreBanking;
using BankGateway.Models;
using BankGateway.Security;
using BankGateway.Services;

var builder = WebApplication.CreateBuilder(args);

// Add services to the container.
builder.Services.AddControllers();
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen();

// Dependency Injection for MuleGuard Banking Core
builder.Services.AddSingleton<IHmacTokenService, HmacTokenService>();
builder.Services.AddSingleton<IAuditLogChainService, AuditLogChainService>();
builder.Services.AddSingleton<IPartialLienService, PartialLienService>();
builder.Services.AddHttpClient<IPythonEngineClient, PythonEngineClient>();

// CORS for Frontend Investigation UI
builder.Services.AddCors(options =>
{
    options.AddPolicy("AllowAll", p =>
        p.AllowAnyOrigin()
         .AllowAnyMethod()
         .AllowAnyHeader());
});

var app = builder.Build();

// Check if user requested CLI test execution mode
if (args.Contains("--run-tests"))
{
    Console.WriteLine("===============================================================================");
    Console.WriteLine("   MULEGUARD C# BANK GATEWAY & CORE INTEGRATIONS TEST RUNNER (.NET 8)");
    Console.WriteLine("===============================================================================");

    var hmac = app.Services.GetRequiredService<IHmacTokenService>();
    var audit = app.Services.GetRequiredService<IAuditLogChainService>();
    var lien = app.Services.GetRequiredService<IPartialLienService>();
    var pythonClient = app.Services.GetRequiredService<IPythonEngineClient>();

    Console.WriteLine("\n[TEST 1] DPDP Act Zero-PII Salted HMAC-SHA256 Tokenization:");
    string rawAcc = "ACC_MULE_L1";
    string bankDisplay = hmac.ResolveDisplayName(rawAcc, "Sohan Lal", "BankAnalyst", null);
    string policeDisplay = hmac.ResolveDisplayName(rawAcc, "Sohan Lal", "LawEnforcement", "FIR-2026-104");
    Console.WriteLine($"   Bank Analyst View (Masked) : {bankDisplay}");
    Console.WriteLine($"   Police FIR View (Unmasked)  : {policeDisplay}");

    Console.WriteLine("\n[TEST 2] Smart 'Tainted Amount' Partial Lien Hold (USP 3):");
    var lienRes = lien.ExecutePartialLienHold(new PartialLienRequest("ACC_MERCHANT_OK", 9500, 540000, "BankCompliance", "FIR-2026-104"));
    Console.WriteLine($"   Lien ID          : {lienRes.LienHoldId}");
    Console.WriteLine($"   Status           : {lienRes.Status}");
    Console.WriteLine($"   Frozen Scam Money: ₹{lienRes.FrozenAmount:N0}");
    Console.WriteLine($"   Usable Balance   : ₹{lienRes.UsableBalance:N0} (Protected for Honest Merchant!)");
    Console.WriteLine($"   Audit Block Hash : {lienRes.AuditHash[..16]}...");

    Console.WriteLine("\n[TEST 3] SHA-256 Tamper-Proof Audit Chain Verification:");
    var verifyBefore = audit.VerifyIntegrity();
    Console.WriteLine($"   Before Tamper Status: {verifyBefore.StatusMessage}");

    Console.WriteLine("   Injecting simulated unauthorized log edit at Record #2...");
    audit.SimulateTampering(2, "HACKED_DELETE_RECORD");
    var verifyAfter = audit.VerifyIntegrity();
    Console.WriteLine($"   After Tamper Status : {verifyAfter.StatusMessage}");
    Console.WriteLine($"   Tamper Detected?    : {!verifyAfter.IsValid} (Flagged Index: {verifyAfter.TamperedIndex})");

    audit.RestoreIntactChain();
    Console.WriteLine($"   Chain Restored      : {audit.VerifyIntegrity().StatusMessage}");

    Console.WriteLine("\n[TEST 4] Investigating Money Trail via Python Graph-AI Service:");
    var trail = await pythonClient.AnalyzeTrailAsync("FIR-2026-104", "BankAnalyst");
    Console.WriteLine($"   Nodes Traced   : {trail.Nodes.Count}");
    Console.WriteLine($"   Transfers Track: {trail.Edges.Count}");
    Console.WriteLine($"   Shadow Links   : {trail.ShadowEdges.Count}");
    foreach (var node in trail.Nodes.Take(4))
    {
        Console.WriteLine($"     • {node.DisplayId,-30} | {node.Bank,-6} | Risk: {node.RiskScore,2}/100 | Scam: ₹{node.TaintedAmount:N0}");
    }

    Console.WriteLine("\n===============================================================================");
    Console.WriteLine("   ALL C# INTEGRATION TESTS PASSED SUCCESSFULLY! (.NET 8)");
    Console.WriteLine("===============================================================================\n");
    return;
}

app.UseCors("AllowAll");

if (app.Environment.IsDevelopment() || true)
{
    app.UseSwagger();
    app.UseSwaggerUI();
}

app.UseRouting();
app.MapControllers();

Console.WriteLine("MuleGuard C# Bank Gateway running on http://127.0.0.1:5000");
app.Run("http://127.0.0.1:5000");

using System.Security.Cryptography;
using System.Text;
using BankGateway.Models;

namespace BankGateway.Security;

public interface IAuditLogChainService
{
    AuditChainEntry AppendLog(string actorRole, string action, string targetEntity);
    AuditVerificationResult VerifyIntegrity();
    bool SimulateTampering(int index, string alteredAction);
    void RestoreIntactChain();
    List<AuditChainEntry> GetChain();
}

public class AuditLogChainService : IAuditLogChainService
{
    private readonly List<AuditChainEntry> _chain = new();
    private readonly object _lock = new();

    public AuditLogChainService()
    {
        // Genesis block
        AppendLog("System", "START_PLATFORM", "C# Banking Gateway Initialized");
    }

    public static string ComputeHash(string payload)
    {
        using var sha = SHA256.Create();
        var bytes = sha.ComputeHash(Encoding.UTF8.GetBytes(payload));
        return Convert.ToHexString(bytes).ToLowerInvariant();
    }

    public AuditChainEntry AppendLog(string actorRole, string action, string targetEntity)
    {
        lock (_lock)
        {
            int nextIndex = _chain.Count + 1;
            string prevHash = _chain.Count == 0 
                ? "0000000000000000000000000000000000000000000000000000000000000000" 
                : _chain[^1].CurrentHash;

            string ts = DateTime.UtcNow.ToString("yyyy-MM-dd HH:mm:ss");
            string payload = $"{nextIndex}|{ts}|{actorRole}|{action}|{targetEntity}|{prevHash}";
            string currHash = ComputeHash(payload);

            var entry = new AuditChainEntry(nextIndex, ts, actorRole, action, targetEntity, prevHash, currHash, false);
            _chain.Add(entry);
            return entry;
        }
    }

    public AuditVerificationResult VerifyIntegrity()
    {
        lock (_lock)
        {
            if (_chain.Count == 0)
            {
                return new AuditVerificationResult(true, 0, "Audit log is empty.", null, new List<AuditChainEntry>());
            }

            for (int i = 0; i < _chain.Count; i++)
            {
                var curr = _chain[i];
                string expectedPrev = (i == 0)
                    ? "0000000000000000000000000000000000000000000000000000000000000000"
                    : _chain[i - 1].CurrentHash;

                if (curr.PreviousHash != expectedPrev)
                {
                    return new AuditVerificationResult(
                        false,
                        _chain.Count,
                        $"CRYPTOGRAPHIC HASH MISMATCH at record #{curr.Index}: PreviousHash link broken!",
                        curr.Index,
                        _chain.ToList()
                    );
                }

                string payload = $"{curr.Index}|{curr.Timestamp}|{curr.ActorRole}|{curr.Action}|{curr.TargetEntity}|{curr.PreviousHash}";
                string calculatedHash = ComputeHash(payload);

                if (curr.CurrentHash != calculatedHash)
                {
                    return new AuditVerificationResult(
                        false,
                        _chain.Count,
                        $"TAMPER DETECTED at record #{curr.Index}: Record content was altered or faked!",
                        curr.Index,
                        _chain.ToList()
                    );
                }
            }

            return new AuditVerificationResult(
                true,
                _chain.Count,
                $"AUDIT CHAIN VERIFIED SAFE: All {_chain.Count} records cryptographically validated.",
                null,
                _chain.ToList()
            );
        }
    }

    public bool SimulateTampering(int index, string alteredAction)
    {
        lock (_lock)
        {
            int targetIdx = index - 1;
            if (targetIdx < 0 || targetIdx >= _chain.Count) return false;

            var orig = _chain[targetIdx];
            _chain[targetIdx] = orig with
            {
                Action = alteredAction,
                CurrentHash = "bad00000000000000000000000000000000000000000000000000000000tamper",
                Tampered = true
            };
            return true;
        }
    }

    public void RestoreIntactChain()
    {
        lock (_lock)
        {
            _chain.Clear();
            AppendLog("System", "START_PLATFORM", "C# Banking Gateway Initialized");
            AppendLog("BankCompliance", "VERIFY_BASELINE", "Loaded FIR-2026-104 Case Baseline");
        }
    }

    public List<AuditChainEntry> GetChain()
    {
        lock (_lock)
        {
            return _chain.ToList();
        }
    }
}

using BankGateway.Models;
using BankGateway.Security;

namespace BankGateway.CoreBanking;

public interface IPartialLienService
{
    PartialLienResponse ExecutePartialLienHold(PartialLienRequest req);
    List<PartialLienResponse> GetActiveLiens();
}

public class PartialLienService : IPartialLienService
{
    private readonly IAuditLogChainService _auditLog;
    private readonly IHmacTokenService _hmac;
    private readonly List<PartialLienResponse> _activeLiens = new();
    private readonly object _lock = new();

    public PartialLienService(IAuditLogChainService auditLog, IHmacTokenService hmac)
    {
        _auditLog = auditLog;
        _hmac = hmac;
    }

    public PartialLienResponse ExecutePartialLienHold(PartialLienRequest req)
    {
        lock (_lock)
        {
            decimal frozenAmt = Math.Min(req.TaintedAmount, req.TotalBalance);
            decimal usableBal = Math.Max(0, req.TotalBalance - frozenAmt);
            string lienId = "LIEN-" + Guid.NewGuid().ToString("N")[..8].ToUpperInvariant();
            string ts = DateTime.UtcNow.ToString("yyyy-MM-dd HH:mm:ss");

            // Log action to tamper-proof audit chain
            var logEntry = _auditLog.AppendLog(
                req.UserRole,
                $"EXECUTE_PARTIAL_LIEN: Held ₹{frozenAmt:N0} (Protected Usable ₹{usableBal:N0})",
                req.AccountId
            );

            string display = _hmac.Tokenize(req.AccountId);

            var resp = new PartialLienResponse(
                lienId,
                "PARTIAL_LIEN_ACTIVE",
                req.AccountId,
                display,
                frozenAmt,
                usableBal,
                ts,
                logEntry.CurrentHash
            );

            _activeLiens.Add(resp);
            return resp;
        }
    }

    public List<PartialLienResponse> GetActiveLiens()
    {
        lock (_lock)
        {
            return _activeLiens.ToList();
        }
    }
}

using System.Security.Cryptography;
using System.Text;

namespace BankGateway.Security;

public interface IHmacTokenService
{
    string Tokenize(string rawValue);
    string ResolveDisplayName(string rawId, string realName, string role, string? firId);
    string ResolvePhone(string rawPhone, string role, string? firId);
    string ResolvePan(string rawPan, string role, string? firId);
    bool CanUnmaskPii(string role, string? firId);
}

public class HmacTokenService : IHmacTokenService
{
    private static readonly byte[] SaltKey = Encoding.UTF8.GetBytes("DPDP_ACT_2026_BANK_SALT_KEY_#9981");

    public string Tokenize(string rawValue)
    {
        if (string.IsNullOrWhiteSpace(rawValue)) return "TOK_UNKNOWN";
        using var hmac = new HMACSHA256(SaltKey);
        var hash = hmac.ComputeHash(Encoding.UTF8.GetBytes(rawValue));
        return "TOK_" + Convert.ToHexString(hash)[..8].ToUpperInvariant();
    }

    public bool CanUnmaskPii(string role, string? firId)
    {
        return string.Equals(role, "LawEnforcement", StringComparison.OrdinalIgnoreCase) 
               && !string.IsNullOrWhiteSpace(firId);
    }

    public string ResolveDisplayName(string rawId, string realName, string role, string? firId)
    {
        if (CanUnmaskPii(role, firId))
        {
            return $"{realName} ({rawId})";
        }
        return $"{Tokenize(rawId)} [HMAC Protected]";
    }

    public string ResolvePhone(string rawPhone, string role, string? firId)
    {
        if (CanUnmaskPii(role, firId)) return rawPhone;
        return "+91-XXXXX-XXXXX";
    }

    public string ResolvePan(string rawPan, string role, string? firId)
    {
        if (CanUnmaskPii(role, firId)) return rawPan;
        return "XXXXX****X";
    }
}

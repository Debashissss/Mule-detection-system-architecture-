using System.Text.Json.Serialization;

namespace BankGateway.Models;

public record ReasonCode(
    [property: JsonPropertyName("label")] string Label,
    [property: JsonPropertyName("pts")] double Pts,
    [property: JsonPropertyName("percentage")] int Percentage
);

public record GraphNodeDto(
    [property: JsonPropertyName("account_id")] string AccountId,
    [property: JsonPropertyName("display_id")] string DisplayId,
    [property: JsonPropertyName("real_name")] string RealName,
    [property: JsonPropertyName("bank")] string Bank,
    [property: JsonPropertyName("device_id")] string DeviceId,
    [property: JsonPropertyName("phone")] string Phone,
    [property: JsonPropertyName("pan")] string Pan,
    [property: JsonPropertyName("total_balance")] decimal TotalBalance,
    [property: JsonPropertyName("tainted_amount")] decimal TaintedAmount,
    [property: JsonPropertyName("safe_balance")] decimal SafeBalance,
    [property: JsonPropertyName("risk_score")] int RiskScore,
    [property: JsonPropertyName("is_flagged_mule")] bool IsFlaggedMule,
    [property: JsonPropertyName("account_type")] string AccountType,
    [property: JsonPropertyName("reasons")] List<ReasonCode> Reasons,
    [property: JsonPropertyName("lien_placed")] bool LienPlaced
);

public record GraphEdgeDto(
    [property: JsonPropertyName("tx_id")] string TxId,
    [property: JsonPropertyName("from_account")] string FromAccount,
    [property: JsonPropertyName("to_account")] string ToAccount,
    [property: JsonPropertyName("amount")] decimal Amount,
    [property: JsonPropertyName("timestamp")] string Timestamp,
    [property: JsonPropertyName("hop")] int Hop
);

public record ShadowEdgeDto(
    [property: JsonPropertyName("from_account")] string FromAccount,
    [property: JsonPropertyName("to_account")] string ToAccount,
    [property: JsonPropertyName("reason")] string Reason,
    [property: JsonPropertyName("identifier")] string Identifier
);

public record InvestigationResult(
    [property: JsonPropertyName("fir_id")] string FirId,
    [property: JsonPropertyName("user_role")] string UserRole,
    [property: JsonPropertyName("is_pii_unmasked")] bool IsPiiUnmasked,
    [property: JsonPropertyName("nodes")] List<GraphNodeDto> Nodes,
    [property: JsonPropertyName("edges")] List<GraphEdgeDto> Edges,
    [property: JsonPropertyName("shadow_edges")] List<ShadowEdgeDto> ShadowEdges,
    [property: JsonPropertyName("audit_hash")] string AuditHash
);

public record PartialLienRequest(
    string AccountId,
    decimal TaintedAmount,
    decimal TotalBalance,
    string UserRole,
    string? FirId
);

public record PartialLienResponse(
    string LienHoldId,
    string Status,
    string AccountId,
    string DisplayId,
    decimal FrozenAmount,
    decimal UsableBalance,
    string Timestamp,
    string AuditHash
);

public record AuditChainEntry(
    int Index,
    string Timestamp,
    string ActorRole,
    string Action,
    string TargetEntity,
    string PreviousHash,
    string CurrentHash,
    bool Tampered = false
);

public record AuditVerificationResult(
    bool IsValid,
    int TotalRecords,
    string StatusMessage,
    int? TamperedIndex,
    List<AuditChainEntry> Chain
);

public record CourtReadyDossier(
    string FirId,
    string GenerationTime,
    string UserRole,
    string CryptographicSignature,
    string InvestigationSummary,
    List<object> AccountsSummary,
    List<string> RecommendedLegalActions
);

export default function QueryButton({ label, sql, runQuery }) {
  return (
    <button
      onClick={() => runQuery(sql)}
      style={{
        margin: "6px",
        padding: "8px 14px",
        borderRadius: "6px",
        border: "1px solid #ccc",
        background: "#1f2937",
        color: "white",
        cursor: "pointer",
        fontSize: "14px"
      }}
    >
      {label}
    </button>
  );
}
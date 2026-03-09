import { useEffect, useState } from "react";
import * as duckdb from "@duckdb/duckdb-wasm";
import { ReactTabulator } from "react-tabulator";
import QueryButton from "./QueryButton";
import "tabulator-tables/dist/css/tabulator.min.css";

export default function App() {
  const [dbConnection, setDbConnection] = useState(null);
  const [query, setQuery] = useState(
    "SELECT * FROM events LIMIT 1000; -- this limit does not take into account Rows to return setting ",
  );

  const BASE = import.meta.env.BASE_URL;
  const [data, setData] = useState([]);
  const [columns, setColumns] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showEditor, setShowEditor] = useState(true);
  const [eventCount, setEventCount] = useState(null);
  const [rowLimit, setRowLimit] = useState(1000);
  const [rowsPerPage, setRowsPerPage] = useState(20);

  const DEBUG_MODE = true;

  const buttonStyle = {
    margin: "6px",
    padding: "8px 14px",
    borderRadius: "6px",
    border: "1px solid #ccc",
    background: "#1f2937",
    color: "#FFFFF0",
    cursor: "pointer",
  };

  // updates query when rowLimit changes
  useEffect(() => {
    setQuery(`SELECT * FROM events LIMIT ${rowLimit};`);
  }, [rowLimit]);

  useEffect(() => {
    async function initDuckDB() {
      try {
        // Fetch versioned asset info
        const versionRes = await fetch(
          `${import.meta.env.BASE_URL}version.json`,
        );
        const version = await versionRes.json(); // e.g. { wasm: "duckdb-v1.wasm", events: "events-v1.parquet", event_files: "event_files-v1.parquet", event_url_list: "event_url_list-v1.parquet" }

        const logger = new duckdb.ConsoleLogger();
        const worker = new Worker(
          `${import.meta.env.BASE_URL}duckdb/duckdb-worker.js`,
          { type: "module" },
        );
        const db = new duckdb.AsyncDuckDB(logger, worker);

        // Instantiate versioned WASM
        await db.instantiate(
          `${import.meta.env.BASE_URL}duckdb/${version.wasm}`,
        );

        const connection = await db.connect();

        // Map table names to versioned Parquet files
        const files = {
          events: version.events,
          event_files: version.event_files,
          event_url_list: version.event_url_list,
        };

        for (const [name, file] of Object.entries(files)) {
          const res = await fetch(`${import.meta.env.BASE_URL}data/${file}`);
          if (!res.ok) throw new Error(`Failed to fetch /data/${file}`);

          const buffer = await res.arrayBuffer();
          const uint8Buffer = new Uint8Array(buffer);

          await db.registerFileBuffer(`${name}.parquet`, uint8Buffer);

          await connection.query(`
          CREATE TABLE ${name} AS SELECT * FROM read_parquet('${name}.parquet')
        `);
        }

        setDbConnection(connection);
        setLoading(false);

        const countRes = await connection.query(
          "SELECT COUNT(*) AS c FROM events",
        );
        setEventCount(countRes.toArray()[0].c);
      } catch (err) {
        console.error("DuckDB init error:", err);
        setLoading(false);
      }
    }

    initDuckDB();
  }, []);
  async function runQuery(sql) {
    if (!dbConnection) return;

    const q = sql || query; // use passed SQL or textarea
    try {
      const result = await dbConnection.query(q);
      const rows = result.toArray();
      setData(rows);

      if (rows.length > 0) {
        const cols = Object.keys(rows[0]).map((key) => ({
          title: key,
          field: key,
          sorter: "string",
        }));
        setColumns(cols);
      } else {
        setColumns([]);
      }
    } catch (err) {
      console.error("Query error:", err);
      setData([]);
      setColumns([]);
    }
  }

  return (
    <div style={{ padding: 40, fontFamily: "sans-serif" }}>
      <h2>DuckDB WASM + Parquet Browser</h2>
      <h4>Data from Statsbomb open data repo</h4>

      <button onClick={() => setShowEditor(!showEditor)} style={buttonStyle}>
        {showEditor ? "SQL Editor ▼" : "SQL Editor ▲"}
      </button>

      {loading && <p>Loading DuckDB and Parquet files...</p>}

      {!loading && (
        <>
          {showEditor && (
            <>
              <textarea
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                style={{
                  width: "100%",
                  height: "150px",
                  fontFamily: "monospace",
                  fontSize: "14px",
                  marginBottom: "10px",
                }}
              />

              <br />
              <button onClick={() => runQuery()} style={buttonStyle}>
                Run Query Above
              </button>

              <hr />
            </>
          )}
          <br />
          <label>Rows to return:</label>

          <input
            type="number"
            value={rowLimit}
            min="1000"
            step="250"
            onChange={(e) => setRowLimit(Number(e.target.value))}
            style={{ marginLeft: "8px", width: "80px" }}
          />

          <label style={{ marginLeft: "20px" }}>Rows per page:</label>

          <input
            type="number"
            value={rowsPerPage}
            min="10"
            step="5"
            onChange={(e) => setRowsPerPage(Number(e.target.value))}
            style={{ marginLeft: "8px", width: "80px" }}
          />

          <QueryButton
            label={`Events (${eventCount ?? "..."})`}
            sql={`SELECT * FROM events LIMIT ${rowLimit}`}
            runQuery={runQuery}
          />
          <QueryButton
            label="Events Summary"
            sql="summarize events;"
            runQuery={runQuery}
          />
          {DEBUG_MODE && (
            <>
              <QueryButton
                label="Event Files"
                sql="SELECT * FROM event_files LIMIT 100"
                runQuery={runQuery}
              />
              <QueryButton
                label="URL List"
                sql="SELECT * FROM event_url_list LIMIT 100"
                runQuery={runQuery}
              />
            </>
          )}
          <br />

          <hr />
          {data.length > 0 && (
            <ReactTabulator
              data={data}
              columns={columns}
              layout="fitData"
              options={{
                movableColumns: true,
                resizableRows: true,
                pagination: "local",
                paginationSize: rowsPerPage,
              }}
            />
          )}
        </>
      )}
    </div>
  );
}

// async function runQuery() {
//   if (!dbConnection) return;

//   try {
//     const result = await dbConnection.query(query);
//     const rows = result.toArray();
//     setData(rows);

//     if (rows.length > 0) {
//       const cols = Object.keys(rows[0]).map((key) => ({
//         title: key,
//         field: key,
//         sorter: "string",
//       }));
//       setColumns(cols);
//     } else {
//       setColumns([]);
//     }
//   } catch (err) {
//     console.error("Query error:", err);
//     setData([]);
//     setColumns([]);
//   }
// }

// import { useEffect, useState } from "react";
// import * as duckdb from "@duckdb/duckdb-wasm";
// // import { ReactTabulator } from "react-tabulator";
// import "tabulator-tables/dist/css/tabulator.min.css"; // Tabulator default CSS
// // import 'react-tabulator/lib/styles.css';
// // import 'react-tabulator/lib/styles.css';
// import { ReactTabulator } from 'react-tabulator'

// export default function App() {

//   const [conn, setConn] = useState(null);
//   const [query, setQuery] = useState(
// `SELECT *
// FROM read_parquet(
// 'https://raw.githubusercontent.com/psime/nzdata/master/nzdata.parquet'
// )
// LIMIT 30;`
//   );

//   const [data, setData] = useState([]);
//   const [columns, setColumns] = useState([]);
//   const [loading, setLoading] = useState(true);

//   useEffect(() => {

//     async function init() {

//       const logger = new duckdb.ConsoleLogger();

//       const worker = new Worker(
//         new URL("./duckdb-worker.js", import.meta.url),
//         { type: "module" }
//       );

//       const db = new duckdb.AsyncDuckDB(logger, worker);

//       const wasmUrl = new URL("./duckdb.wasm", import.meta.url).toString();

//       await db.instantiate(wasmUrl);

//       const connection = await db.connect();

//       setConn(connection);
//       setLoading(false);
//     }

//     init();

//   }, []);

//   async function runQuery() {
//     if (!conn) return;

//     const result = await conn.query(query);
//     const rows = result.toArray();

//     setData(rows);

//     if (rows.length > 0) {
//       const cols = Object.keys(rows[0]).map(key => ({
//         title: key,
//         field: key,
//         sorter: "string",
//       }));
//       setColumns(cols);
//     } else {
//       setColumns([]);
//     }
//   }

//   return (
//     <div style={{ padding: 40, fontFamily: "sans-serif" }}>

//       <h2>DuckDB SQL with Tabulator</h2>

//       {loading && <p>Loading DuckDB...</p>}

//       {!loading && (
//         <>
//           <textarea
//             value={query}
//             onChange={(e) => setQuery(e.target.value)}
//             style={{
//               width: "100%",
//               height: "150px",
//               fontFamily: "monospace",
//               fontSize: "14px",
//               marginBottom: "10px"
//             }}
//           />

//           <br />

//           <button onClick={runQuery}>Run Query</button>

//           <hr />

//           {data.length > 0 && (
//             <ReactTabulator
//               data={data}
//               columns={columns}
//               layout="fitData"
//               options={{
//                 movableColumns: true,
//                 resizableRows: true,
//                 pagination: "local",
//                 paginationSize: 10,
//               }}
//             />
//           )}
//         </>
//       )}

//     </div>
//   );
// }

import { useEffect, useState } from "react";
import * as duckdb from "@duckdb/duckdb-wasm";
import { ReactTabulator } from "react-tabulator";
import QueryButton from "./QueryButton";
import "tabulator-tables/dist/css/tabulator.min.css";

export default function App() {
  const [dbConnection, setDbConnection] = useState(null);
  const [query, setQuery] = useState("SELECT * FROM events LIMIT 30;");
  const [data, setData] = useState([]);
  const [columns, setColumns] = useState([]);
  const [loading, setLoading] = useState(true);
  const DEBUG_MODE = false;

  useEffect(() => {
    async function initDuckDB() {
      try {
        // Create the DuckDB worker and WASM instance
        const logger = new duckdb.ConsoleLogger();
        const worker = new Worker("/duckdb/duckdb-worker.js", { type: "module" });
        const db = new duckdb.AsyncDuckDB(logger, worker);
        await db.instantiate("/duckdb/duckdb.wasm");

        // Connect to the database
        const connection = await db.connect();

        // Parquet files to load
        const files = ['events', 'event_files', 'event_url_list'];

        for (const name of files) {
          const res = await fetch(`/data/${name}.parquet`);
          if (!res.ok) throw new Error(`Failed to fetch /data/${name}.parquet`);
          
          const buffer = await res.arrayBuffer();
          const uint8Buffer = new Uint8Array(buffer); // <-- convert to Uint8Array

          await db.registerFileBuffer(`${name}.parquet`, uint8Buffer);

          await connection.query(`
            CREATE TABLE ${name} AS SELECT * FROM read_parquet('${name}.parquet')
          `);
        }

        setDbConnection(connection);
        setLoading(false);
      } catch (err) {
        console.error("DuckDB init error:", err);
        setLoading(false);
      }
    }

    initDuckDB();
  }, []);

  async function runQuery(sql) {
    if (!dbConnection) return;


    const q = sql || query;   // use passed SQL or textarea
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
      <h2>DuckDB WASM + Parquet Browser Test</h2>

      {loading && <p>Loading DuckDB and Parquet files...</p>}

      {!loading && (
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

          <button onClick={() => runQuery()}
                  style={{
                  margin: "6px",
                  padding: "8px 14px",
                  borderRadius: "6px",
                  border: "1px solid #ccc",
                  background: "#1f2937",
                  color: "white",
                  cursor: "pointer",
                  fontSize: "14px"
                }}>Run Query
          </button>
          <hr />
             <QueryButton
              label="Events"
              sql="SELECT * exclude(event_id) FROM events LIMIT 3000"
              runQuery={runQuery}
            />
              <QueryButton
              label="Events Summary"
              sql="summarize events;"
              runQuery={runQuery}
            />
            {DEBUG_MODE && (
              <QueryButton
              label="Event Files"
              sql="SELECT * FROM event_files LIMIT 100"
              runQuery={runQuery}
            />
            )}
           {DEBUG_MODE && (
             <QueryButton
              label="URL List"
              sql="SELECT * FROM event_url_list LIMIT 100"
              runQuery={runQuery}
            />
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
                paginationSize: 50,
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
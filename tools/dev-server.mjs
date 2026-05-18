import { createReadStream, existsSync, statSync } from "node:fs";
import { createServer } from "node:http";
import { extname, join, normalize, resolve, sep } from "node:path";

const root = resolve(process.cwd());
const host = process.env.HOST;
const preferredPort = Number(process.env.PORT || 5173);

const contentTypes = {
  ".css": "text/css; charset=utf-8",
  ".geojson": "application/geo+json; charset=utf-8",
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".webmanifest": "application/manifest+json; charset=utf-8",
};

const server = createServer((request, response) => {
  const url = new URL(
    request.url || "/",
    `http://${request.headers.host || `localhost:${preferredPort}`}`,
  );
  let pathname = decodeURIComponent(url.pathname);

  if (pathname === "/") {
    response.writeHead(302, { Location: "/pwa/" });
    response.end();
    return;
  }

  if (pathname.endsWith("/")) {
    pathname = `${pathname}index.html`;
  }

  const requestedPath = normalize(pathname).replace(/^([/\\])+/, "");
  const filePath = resolve(join(root, requestedPath));
  const rootWithSeparator = root.endsWith(sep) ? root : `${root}${sep}`;

  if (filePath !== root && !filePath.startsWith(rootWithSeparator)) {
    response.writeHead(403, { "Content-Type": "text/plain; charset=utf-8" });
    response.end("Forbidden");
    return;
  }

  if (!existsSync(filePath) || !statSync(filePath).isFile()) {
    response.writeHead(404, { "Content-Type": "text/plain; charset=utf-8" });
    response.end("Not found");
    return;
  }

  response.writeHead(200, {
    "Cache-Control": "no-store",
    "Content-Type": contentTypes[extname(filePath)] || "application/octet-stream",
  });
  createReadStream(filePath).pipe(response);
});

function listen(port) {
  server.once("error", (error) => {
    if (error.code === "EADDRINUSE" && !process.env.PORT) {
      listen(port + 1);
      return;
    }
    throw error;
  });

  const onListening = () => {
    const displayHost = host || "localhost";
    console.log(`mapping_Paris dev server running at http://${displayHost}:${port}/pwa/`);
  };

  if (host) {
    server.listen(port, host, onListening);
  } else {
    server.listen(port, onListening);
  }
}

listen(preferredPort);

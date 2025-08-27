# NovaTime Swagger UI Bundle

Static Swagger UI for hosting behind any static server (S3, GitHub Pages, nginx).

## Files
- `index.html` — loads Swagger UI via CDN and points to `novatime_openapi_v1.1.yaml`
- `swagger-initializer.js` — bootstraps SwaggerUIBundle config
- `novatime_openapi_v1.1.yaml` — the API spec

> Note: This bundle references Swagger UI assets from a public CDN.
> It requires internet access to load `swagger-ui-dist` JS/CSS.

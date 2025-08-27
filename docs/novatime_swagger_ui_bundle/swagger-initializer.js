
window.onload = () => {
  window.ui = SwaggerUIBundle({
    url: './novatime_openapi_v1.1.yaml',
    dom_id: '#swagger-ui',
    presets: [SwaggerUIBundle.presets.apis, SwaggerUIStandalonePreset],
    layout: 'BaseLayout',
    deepLinking: true,
    tryItOutEnabled: true,
    docExpansion: 'list',
    filter: true
  });
};

/**
 * GraphiQL bootstrap + custom plugins (Examples + Show SDL)
 *
 * Expected globals (UMD):
 *   - React, ReactDOM, GraphiQL
 *   - (optional) GraphiQLPluginExplorer (if explorer plugin is enabled & loaded)
 * Expected config:
 *   window.__GRAPHIQL_CONFIG__ = {
 *     defaultQuery: string,
 *     enableExplorerPlugin: boolean,
 *     sdlUrl?: string,          // default: "/sdl"
 *     rootElId?: string,        // default: "graphiql"
 *   }
 * Expected examples:
 *   window.GRAPHIQL_EXAMPLES = [...] (from /static/graphiql_examples.js)
 */

(function () {
  "use strict";

  // Config is injected by the HTML template at runtime.
  var CFG = window.__GRAPHIQL_CONFIG__ || {};
  var ROOT_EL_ID = CFG.rootElId || "graphiql";
  var SDL_URL = CFG.sdlUrl || "/sdl";
  var ENABLE_EXPLORER = !!CFG.enableExplorerPlugin;
  // Default query shows up in the editor on first load.
  var DEFAULT_QUERY = CFG.defaultQuery || "";

  // GraphiQL fetcher (keeps existing behavior: post to the current URL)
  var fetcher = GraphiQL.createFetcher({
    url: window.location.href,
  });

  // Examples live in a separate static file so the HTML template stays small.
  var EXAMPLES = window.GRAPHIQL_EXAMPLES || [];
  // Cached "details open" state so collapsing a section doesn't reset on rerender.
  var EXAMPLES_OPEN_MAP = null;

  function ExamplesIcon() {
    return React.createElement(
      "svg",
      { width: 18, height: 18, viewBox: "0 0 24 24", fill: "none" },
      React.createElement("path", {
        d: "M4 6h16M4 12h16M4 18h10",
        stroke: "currentColor",
        strokeWidth: 2,
        strokeLinecap: "round",
      })
    );
  }

  function sectionKey(group, index) {
    return (group && group.section) || "section-" + index;
  }

  // Cache which sections are expanded so toggles persist while the page is open.
  function buildDefaultOpenMap(groups) {
    var map = {};
    (groups || []).forEach(function (group, index) {
      map[sectionKey(group, index)] = true;
    });
    return map;
  }

  function getExamplesOpenMap() {
    if (!EXAMPLES_OPEN_MAP) {
      EXAMPLES_OPEN_MAP = buildDefaultOpenMap(EXAMPLES);
    }
    return EXAMPLES_OPEN_MAP;
  }

  function SdlIcon() {
    return React.createElement(
      "svg",
      { width: 18, height: 18, viewBox: "0 0 24 24", fill: "none" },
      React.createElement("path", {
        d: "M8 6h13M8 10h13M8 14h13M8 18h13M3 6h2M3 10h2M3 14h2M3 18h2",
        stroke: "currentColor",
        strokeWidth: 2,
        strokeLinecap: "round",
      })
    );
  }

  // Custom "Examples" sidebar plugin:
  // - Supports both grouped and flat example formats
  // - Loads query + variables into the editors
  // - Re-opens the panel if GraphiQL auto-collapses it after a click
  function makeExamplesPlugin(setQuery, setVariables) {
    function ensureExamplesOpen() {
      var btn = document.querySelector('button[aria-label="Show Examples"]');
      if (btn) btn.click();
    }

    return {
      title: "Examples",
      icon: ExamplesIcon,
      content: function ExamplesPanel() {
        var _a = React.useState(function () {
            return getExamplesOpenMap();
          }),
          openMap = _a[0],
          setOpenMap = _a[1];

        // Clicking an example should load both query and variables.
        function renderExampleButton(ex) {
          return React.createElement(
            "button",
            {
              key: ex.name,
              className: "examples-btn",
              onClick: function () {
                setQuery(ex.query || "");
                setVariables(ex.variables || "{}");
                // If GraphiQL auto-closes the plugin, reopen the Examples panel.
                window.requestAnimationFrame(ensureExamplesOpen);
              },
            },
            React.createElement("div", null, ex.name || "Untitled"),
            React.createElement(
              "div",
              { className: "examples-desc" },
              ex.description || ""
            )
          );
        }

        // Detect grouped format: [{ section, items: [...] }, ...]
        var isGrouped =
          Array.isArray(EXAMPLES) &&
          EXAMPLES.length > 0 &&
          EXAMPLES[0] &&
          typeof EXAMPLES[0] === "object" &&
          Array.isArray(EXAMPLES[0].items);

        // Flat fallback for older example lists.
        if (!isGrouped) {
          return React.createElement(
            "div",
            { className: "examples-panel" },
            React.createElement("h3", null, "Examples"),
            React.createElement(
              "div",
              { className: "examples-list" },
              (EXAMPLES || []).map(renderExampleButton)
            )
          );
        }

        // Grouped rendering with collapsible sections.
        return React.createElement(
          "div",
          { className: "examples-panel" },
          React.createElement("h3", null, "Examples"),
          (EXAMPLES || []).map(function (group, index) {
            var key = sectionKey(group, index);
            return React.createElement(
              "details",
              {
                key: key,
                className: "examples-section",
                open: !!openMap[key],
                onToggle: function (event) {
                  var isOpen = event.currentTarget.open;
                  setOpenMap(function (prev) {
                    var next = Object.assign({}, prev);
                    next[key] = isOpen;
                    EXAMPLES_OPEN_MAP = next;
                    return next;
                  });
                },
              },
              React.createElement("summary", null, group.section || "Section"),
              React.createElement(
                "div",
                { className: "examples-list" },
                (group.items || []).map(renderExampleButton)
              )
            );
          })
        );
      },
    };
  }

  // "SDL" plugin (loads from a server endpoint like /sdl).
  // Exposes load/copy/download to make schema inspection easier.
  function makeSdlPlugin() {
    return {
      title: "SDL",
      icon: SdlIcon,
      content: function SdlPanel() {
        var _a = React.useState(false),
          loading = _a[0],
          setLoading = _a[1];
        var _b = React.useState(""),
          error = _b[0],
          setError = _b[1];
        var _c = React.useState(""),
          sdl = _c[0],
          setSdl = _c[1];

        async function loadSDL() {
          setLoading(true);
          setError("");

          try {
            var res = await fetch(SDL_URL, { method: "GET" });
            if (!res.ok) {
              var text = await res.text().catch(function () {
                return "";
              });
              throw new Error(
                "Failed to load " +
                  SDL_URL +
                  " (" +
                  res.status +
                  "): " +
                  (text || res.statusText)
              );
            }
            var body = await res.text();
            setSdl(body);
          } catch (e) {
            setError(e && e.message ? e.message : String(e));
          } finally {
            setLoading(false);
          }
        }

        async function copySDL() {
          try {
            await navigator.clipboard.writeText(sdl || "");
          } catch (e) {
            alert(
              "Copy failed. You can manually select and copy the SDL text."
            );
          }
        }

        function downloadSDL() {
          var blob = new Blob([sdl || ""], { type: "text/plain;charset=utf-8" });
          var url = URL.createObjectURL(blob);
          var a = document.createElement("a");
          a.href = url;
          a.download = "schema.graphql";
          document.body.appendChild(a);
          a.click();
          a.remove();
          URL.revokeObjectURL(url);
        }

        return React.createElement(
          "div",
          { className: "sdl-panel" },
          React.createElement("h3", null, "Schema SDL"),
          React.createElement(
            "div",
            { className: "sdl-actions" },
            React.createElement(
              "button",
              { className: "sdl-btn", onClick: loadSDL, disabled: loading },
              loading ? "Loading..." : sdl ? "Reload SDL" : "Load SDL"
            ),
            React.createElement(
              "button",
              {
                className: "sdl-btn",
                onClick: copySDL,
                disabled: !sdl || loading,
              },
              "Copy"
            ),
            React.createElement(
              "button",
              {
                className: "sdl-btn",
                onClick: downloadSDL,
                disabled: !sdl || loading,
              },
              "Download"
            )
          ),
          error
            ? React.createElement(
                "div",
                { className: "sdl-hint", style: { color: "#ffb3b3" } },
                error
              )
            : null,
          React.createElement("textarea", {
            className: "sdl-textarea",
            readOnly: true,
            value: sdl || "",
            placeholder: "Click “Load SDL” to fetch " + SDL_URL + " and show the schema.",
          }),
          React.createElement(
            "div",
            { className: "sdl-hint" },
            // "If " + SDL_URL + " returns 404/403, it may be disabled in this environment."
            "Tip: Feel free to use ",
            React.createElement(
              "a",
              {
                href: "https://apis.guru/graphql-voyager/",
                target: "_blank",
                rel: "noreferrer",
              },
              "graphql-voyager"
            ),
            " to visualize the schema."
          )
        );
      },
    };
  }

  function AriadneGraphiQL() {
    var _a = React.useState(DEFAULT_QUERY),
      query = _a[0],
      setQuery = _a[1];
    var _b = React.useState("{}"),
      variables = _b[0],
      setVariables = _b[1];

    // Optional explorer plugin is only enabled if the bundle is loaded.
    var explorerPlugin = null;
    if (ENABLE_EXPLORER && window.GraphiQLPluginExplorer) {
      explorerPlugin = GraphiQLPluginExplorer.useExplorerPlugin({
        query: query,
        onEdit: setQuery,
      });
    }

    // Custom plugins are always appended after the optional explorer plugin.
    var examplesPlugin = makeExamplesPlugin(setQuery, setVariables);
    var sdlPlugin = makeSdlPlugin();

    var plugins = [];
    if (explorerPlugin) plugins.push(explorerPlugin);
    plugins.push(examplesPlugin);
    plugins.push(sdlPlugin);

    // Open Examples by default (matches the prior HTML toggle behavior).
    React.useEffect(function () {
      var btn =
        document.querySelector('button[aria-label="Show Examples"]') ||
        document.querySelector('button[data-index="3"]');
      if (btn && !btn.classList.contains("active")) btn.click();
    }, []);

    return React.createElement(GraphiQL, {
      fetcher: fetcher,
      defaultEditorToolsVisibility: true,
      plugins: plugins,

      query: query,
      onEditQuery: setQuery,

      variables: variables,
      onEditVariables: setVariables,
      },
      React.createElement(GraphiQL.Logo, null, "Core API")
    );
  }

  // Mount
  var root = document.getElementById(ROOT_EL_ID);
  if (!root) {
    console.error("GraphiQL root element not found:", ROOT_EL_ID);
    return;
  }

  ReactDOM.render(React.createElement(AriadneGraphiQL), root);
})();

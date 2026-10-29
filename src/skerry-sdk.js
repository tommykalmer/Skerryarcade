/* Skerry SDK: the small bridge between a game and the Skerry Arcade portal.
   Include it in a game that lives on the portal:  <script src="/assets/skerry-sdk.js"></script>
   Every call is safe outside the portal (opened directly, on another site): it then does nothing,
   and save/load fall back to plain localStorage.

     SkerrySDK.gameplayStart()                  the player is actually playing (round started)
     SkerrySDK.gameplayStop()                   paused, menu, round over
     SkerrySDK.levelEnd(level, "win", score)    a level, round or daily puzzle finished
     SkerrySDK.happytime()                      a big moment: record, win, unlock
     SkerrySDK.event("powerup_used", {...})     anything else worth counting (name: letters, digits, _)
     SkerrySDK.save("key", value) / load("key", fallback)
*/
(function () {
  "use strict";
  var queue = [], host = null;
  function findHost() {
    try { if (window.SkerryHost) return window.SkerryHost; } catch (e) {}
    try { if (window.parent && window.parent !== window && window.parent.location.host === location.host) return null; } catch (e) {}
    return null;
  }
  function flush() {
    host = window.SkerryHost || null;
    if (!host) return;
    while (queue.length) { var c = queue.shift(); try { host[c[0]].apply(host, c[1]); } catch (e) {} }
  }
  function call(name) {
    var args = Array.prototype.slice.call(arguments, 1);
    if (host || (host = findHost())) { try { host[name].apply(host, args); } catch (e) {} }
    else if (window.parent !== window) { queue.push([name, args]); if (queue.length > 50) queue.shift(); }
  }
  window.addEventListener("skerryhost", flush);
  var prefix = "skerry." + (location.pathname.split("/")[2] || "game") + ".";
  window.SkerrySDK = {
    gameplayStart: function () { call("gameplayStart"); },
    gameplayStop: function () { call("gameplayStop"); },
    happytime: function () { call("happytime"); },
    levelEnd: function (level, result, score) { call("levelEnd", level, result, score); },
    event: function (name, params) { call("event", name, params || {}); },
    save: function (key, value) { try { localStorage.setItem(prefix + key, JSON.stringify(value)); } catch (e) {} },
    load: function (key, fallback) { try { var v = localStorage.getItem(prefix + key); return v == null ? fallback : JSON.parse(v); } catch (e) { return fallback; } },
    get onPortal() { return !!(host || window.SkerryHost); }
  };
})();

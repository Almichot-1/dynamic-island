import QtQuick
import Quickshell.Services.Notifications

// What the companion falls back on when Omarchy's own notification service
// can't be loaded (see Service.qml): a bare server that keeps banners coming
// to the island, so nothing is lost. It has no stacks, actions, Do Not
// Disturb memory or history; those come from the native service.
Item {
  id: fallback
  // Feed rows (see Service.qml), newest first.
  property var rows: []
  property bool doNotDisturb: false
  property var refs: ({})
  property var retained: []
  property int seq: 0

  NotificationServer {
    keepOnReload: false
    imageSupported: true
    actionsSupported: true
    onNotification: function(n) { fallback.take(n) }
  }

  function take(n) {
    if (doNotDisturb && n.urgency !== NotificationUrgency.Critical) { n.tracked = false; return }
    // Otherwise the object is destroyed when this handler returns.
    n.tracked = true
    var existing = Object.keys(refs).filter(function(k) { return refs[k] === n })
    var key = existing.length ? existing[0] : "fallback" + Date.now().toString(36) + (++seq)
    refs[key] = n
    if (!existing.length) n.closed.connect(function() {
      delete fallback.refs[key]
      fallback.retained = fallback.retained.filter(function(k) { return k !== key })
      fallback.rows = fallback.rows.filter(function(r) { return r.key !== key })
    })
    retained = [key].concat(retained.filter(function(k) { return k !== key }))
    while (retained.length > 100) dismiss(retained[retained.length - 1])
    var normal = n.urgency !== NotificationUrgency.Critical
    rows = [{ key: key, originalId: n.id, timestamp: Date.now(), app: n.appName, appIcon: n.appIcon, image: n.image,
              desktopEntry: n.desktopEntry, codexThread: String(n.hints["x-island-codex-thread"] || ""),
              glyph: "", summary: n.summary, body: String(n.body).replace(/<[^>]+>/g, " ").replace(/\s+/g, " ").trim(), urgency: n.urgency,
              group: "", stack: 1, actions: [], duration: normal ? Math.max(8000, n.expireTimeout) : 0 }].concat(rows.filter(function(r) { return r.key !== key }))
  }

  // The sender's default action, if it has one; either way the banner goes.
  function invoke(key) {
    var n = refs[key]
    for (var i = 0; n && i < n.actions.length; i++)
      if (String(n.actions[i].identifier) === "default") { hide(key); n.actions[i].invoke(); return true }
    dismiss(key)
    return false
  }
  // End only the banner. Keep its sender's action available in history.
  function hide(key) { rows = rows.filter(function(r) { return r.key !== key }) }
  function dismiss(key) { if (refs[key]) refs[key].dismiss() }
}

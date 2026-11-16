import QtQuick
import QtQuick.Window
import QtQuick.Layouts
import Quickshell
import "../../components" as UI
import "../../addons/agents" as Agents
import "../../addons/plugins" as Plugins

// A separate, offscreen showcase using the shipped components and sample data.
// Nothing here reads live sessions, notifications, media, or desktop contents.
Window {
  id: movie
  visible: true
  width: 1280; height: 720
  color: "#141820"
  property int frame: 0
  property int fps: 25
  readonly property real seconds: frame / fps
  readonly property int scene: seconds < 5 ? 0 : seconds < 14 ? 1 : seconds < 22 ? 2 : seconds < 30 ? 3 : seconds < 37 ? 4 : seconds < 44 ? 5 : 6
  readonly property real local: seconds - [0,5,14,22,30,37,44][scene]
  property bool busy: false
  readonly property bool expanded: (scene === 2 && local > 2 && local < 6) || scene === 3 || scene === 5
  readonly property bool mediaVisible: scene !== 1 && scene !== 4 && !(scene === 2 && !expanded)
  readonly property string output: Quickshell.env("ISLAND_DEMO_FRAMES")
  readonly property var headings: ["Your desktop. In motion.","From clone to your desktop.","There when you need it.","Pause. Hover. Press play.","Every session. One place.","Stay in the flow.","Make your desktop feel alive."]
  readonly property var captions: ["Dynamic Island for Omarchy, with Codex built in.","One installer applies the profile, helpers, and integrations.","A tiny handle over apps. Hover to reveal. Move away to tuck it back.","Paused media stays ready. Play and pause straight from the hover panel.","See who is working, who needs you, and jump to the right terminal.","Actionable alerts, preserved media, and a readable next-prayer tile.","Get Dynamic Island. Share it. Make it yours."]

  QtObject {
    id: demoTheme
    property string fontFamily: "JetBrainsMono Nerd Font"
    property string textFontFamily: "Adwaita Sans"
    property color background: "#000000"
    property color text: "#e6e6e6"
    property color secondary: "#90949d"
    property color accent: "#f4cc49"
    property color accentText: "#171b24"
    property color card: "#141414"
    property color wellHover: "#292929"
    property color hairline: "#242424"
    property var system: ({blue:"#0a84ff",orange:"#ff9f0a",green:"#30d158"})
    property var size: ({title3:15,body:13,subheadline:11})
    function px(n) { return n }
    function tracking(f,n) { return 0 }
    function motionDuration(p) { return p === "expressive" ? 420 : p === "exit" ? 180 : 260 }
    function motionCurve(p) { return [0.16,1,0.3,1,1,1] }
    function scaled(n) { return n }
    function withAlpha(c,a) { return Qt.rgba(c.r,c.g,c.b,a) }
  }
  QtObject {
    id: media
    property bool playing: !(movie.scene === 3 && movie.local < 4)
    property bool available: true
    property string title: "Night Drive"
    property string artist: "Demo track"
    property string art: Qt.resolvedUrl("cover.svg")
    property color tint: "#f4cc49"
    property var player: ({trackArtist: "Demo track"})
    function togglePlaying() { playing = !playing }
  }
  QtObject {
    id: demoSettings
    property bool notch: false
    property bool glanceMediaSatellite: true
    property bool glanceMediaSatelliteBorder: true
    property bool notificationButtons: false
    property bool notificationFullText: false
    property bool stackNotifications: false
  }
  QtObject {
    id: notes
    property var last: ({app:"Codex",summary:"Codex needs your input",body:"Demo project · Ready for your review",timestamp:0})
    function iconSource(r,e) { return "" }
    function brand(r) { return {glyph:"",tile:"#f2f2f2",ink:"#000000"} }
    function title(r) { return r.summary }
    function age(t) { return "now" }
    function open(r,l) {}
  }
  QtObject {
    id: demoHost
    property var theme: demoTheme
    property var nowPlaying: media
    property var settings: demoSettings
    property var notifications: notes
    property string view: "rest"
    property bool mediaPill: movie.mediaVisible && !movie.expanded
    property bool notificationPill: movie.scene === 5 && movie.local > 1.5
    property int pillHeight: 44
    function dismissFeedback() {}
  }
  QtObject {
    id: look
    property var host: demoHost
    property color text: demoTheme.text
    property color textMuted: demoTheme.secondary
    property color card: demoTheme.card
    property color edge: demoTheme.hairline
  }
  QtObject {
    id: demoAgents
    property var sessions: [
      {id:"demo-web-session",label:"Build the dashboard",project:"web-app",state:"working",reason:""},
      {id:"demo-api-session",label:"Review the API changes",project:"api",state:"asking",reason:"input"},
      {id:"demo-docs-session",label:"Update the docs",project:"docs",state:"idle",reason:""}
    ]
    function openSession(id) {}
  }
  QtObject {
    id: demoCenter
    property var host: demoHost
    property int tileHeight: 64
    property int cardRadius: 14
    property color tile: "#222222"
    property color card: demoTheme.card
    property color edge: demoTheme.hairline
    property color accent: demoTheme.accent
    property color well: "#252525"
    property color text: demoTheme.text
    property color textMuted: demoTheme.secondary
    property color badgeOnInk: "#382e09"
    property string iconFont: demoTheme.fontFamily
  }
  QtObject {
    id: salah
    property string prayerName: "Asr"
    property string countdown: "24m"
  }
  QtObject {
    id: demoBarWidgets
    function widget(id) { return salah }
  }
  QtObject {
    id: pluginHost
    property var barWidgets: demoBarWidgets
  }
  QtObject {
    id: pluginAddon
    property var host: pluginHost
    property var keysById: ({})
    function iconOf(id) { return {text:"󰖨",family:demoTheme.fontFamily} }
    function open(e) {}
    function setEnabled(e,v) {}
  }

  Item {
    id: canvas
    anchors.fill: parent
    Rectangle { anchors.fill: parent; color: "#141820" }
    Rectangle { x:64; y:48; width:42; height:18; radius:9; color:demoTheme.accent }
    Text { x:120; y:40; text:"Dynamic Island"; color:"#f7f7f7"; font.family:demoTheme.textFontFamily; font.pixelSize:28; font.weight:Font.DemiBold }
    Text { anchors.right:parent.right; anchors.rightMargin:64; y:51; text: ["Meet Island","Install","Hover reveal","Media","Codex","Notifications","Get it"][movie.scene]; color:demoTheme.secondary; font.family:demoTheme.textFontFamily; font.pixelSize:17 }

    Rectangle {
      id: desktop
      x:120; y:110; width:1040; height:370; radius:20
      color:"#1c222d"; border.color:"#333a46"
      clip:true
      Text { x:28; y:22; text: movie.scene === 1 ? "Install on Omarchy" : "Demo workspace"; color:"#949eae"; font.family:demoTheme.textFontFamily; font.pixelSize:16 }
      Rectangle { x:24; y:66; width:300; height:276; radius:12; color:"#222a37"; visible:movie.scene !== 1 && movie.scene !== 4 }
      Text { x:48; y:92; visible: movie.scene !== 1 && movie.scene !== 4; text:"dynamic-island/\n\n  addons/\n  components/\n  scripts/\n  install.py\n  README.md"; lineHeight:1.25; color:"#9aa7b8"; font.family:demoTheme.textFontFamily; font.pixelSize:19 }
      Rectangle { x:344; y:66; width:670; height:276; radius:12; color:"#202733"; visible:movie.scene !== 1 && movie.scene !== 4 }
      Text {
        x:380; y:164; visible:movie.scene !== 1 && movie.scene !== 4
        text:"def install(home, hooks=False):\n    config = home / '.config/omarchy'\n    settings.update(\n        mediaPill=True,\n        autoHideTiling=True,\n        hoverStyle='expand'\n    )"
        lineHeight:1.35; color:"#9aa7b8"; font.family:demoTheme.fontFamily; font.pixelSize:18
      }
      Column {
        x:46; y:104; spacing:25; visible:movie.scene === 1
        Repeater {
          model:["git clone https://github.com/Almichot-1/dynamic-island.git","cd dynamic-island","python3 install.py --activate --hooks --with-salah"]
          Text { required property string modelData; required property int index; text: "> " + modelData.slice(0,Math.max(0,Math.floor((movie.local-index*1.6)*45))); color:index===2 ? demoTheme.accent : "#e5e9ef"; font.family:demoTheme.fontFamily; font.pixelSize:21 }
        }
        Text { text:"Then review /hooks once in Codex."; color:"#9ca6b5"; font.family:demoTheme.textFontFamily; font.pixelSize:18; opacity:movie.local>5.8 ? 1:0 }
      }
      Rectangle {
        id: island
        readonly property real targetHeight: height
        readonly property bool isGlanceExpanded: movie.expanded
        x:(parent.width-width)/2
        y:movie.scene === 2 && !movie.expanded ? -46 : 18
        width: movie.scene === 4 ? 540 : movie.expanded ? 480 : 280
        height:movie.scene === 4 ? 306 : 48
        radius:movie.scene === 4 ? 24 : 28
        color:"#000000"
        visible:movie.scene!==1
        Behavior on y { UI.MotionAnimation { theme:demoTheme } }
        Behavior on width { UI.MotionAnimation { theme:demoTheme } }
        Behavior on height { UI.MotionAnimation { theme:demoTheme } }
        UI.MediaPill { anchors.fill:parent; host:demoHost; shape:island }
        // Software capture cannot paint Quickshell's GPU clipping material.
        // Overlay the same sample artwork in its exact media-cover position.
        Image { x:8; y:9; width:30; height:30; source:media.art; visible:demoHost.mediaPill }
        Text { anchors.centerIn:parent; text:movie.expanded ? "2 sessions    ·    14:28    ·    85%" : "14:28"; visible:movie.scene!==4; color:"#ececec"; font.family:demoTheme.textFontFamily; font.pixelSize:17; font.weight:Font.Medium }
        Agents.CodexSessionList { x:18; y:20; width:parent.width-36; visible:movie.scene===4; agents:demoAgents; view:look }
      }
      Rectangle { anchors.horizontalCenter:parent.horizontalCenter; y:1; width:48; height:3; radius:2; color:"#a3a9b3"; visible:movie.scene===2 && !movie.expanded }
      UI.MediaSatellitePill {
        id: demoSatellite
        host:demoHost; shape:island
        Image { x:12; y:6; width:18; height:18; source:media.art }
      }
      Rectangle {
        x:island.x+island.width+10; y:island.y+8; width:64; height:32; radius:16
        color:"black"; visible:movie.scene!==1 && movie.scene!==4 && !(movie.scene===2 && !movie.expanded)
        Text { anchors.centerIn:parent; text:" 2"; font.family:demoTheme.fontFamily; font.pixelSize:17; color:demoTheme.system.blue }
      }
      Rectangle {
        x:300; y:movie.scene===5 && movie.local>1.5 ? 122:98; width:440; height:84; radius:18; color:"black"
        visible:movie.scene===5 && movie.local>1.5
        Behavior on y { UI.MotionAnimation { theme:demoTheme } }
        UI.NotificationPill { anchors.fill:parent; host:demoHost; shape:parent }
        Rectangle { x:15; y:15; width:54; height:54; radius:15; color:"#f2f2f2"
          Text { anchors.centerIn:parent; text:""; font.family:demoTheme.fontFamily; font.pixelSize:32; color:"black" }
        }
      }
      RowLayout {
        x:300; y:234; width:440; spacing:12; visible:movie.scene===5 && movie.local>3.5
        Plugins.PluginTile { addon:pluginAddon; center:demoCenter; entry:({id:"salah.reminder",name:"Salah Reminder",enabled:true,openable:true}) }
        UI.SoundWave { playing:true; color:demoTheme.accent; Layout.preferredWidth:80; Layout.preferredHeight:18 }
      }
      Rectangle {
        x:770; y:152; width:225; height:112; radius:12; color:"#161b24"
        visible:movie.scene===4 && movie.local>3.8
        Text { anchors.fill:parent; anchors.margins:16; text:"api / Codex\n\nReady for your input"; color:"#e6e6e6"; font.family:demoTheme.textFontFamily; font.pixelSize:16 }
      }
      Text {
        x:movie.scene===3 ? 602 : movie.scene===4 ? 670 : 500
        y:movie.scene===3 ? 88 : movie.scene===4 ? 176 : 8
        text:"󰇀"; color:"white"; font.family:demoTheme.fontFamily; font.pixelSize:29
        visible:(movie.scene===2 && movie.expanded) || movie.scene===3 || (movie.scene===4 && movie.local>3)
      }
      Rectangle {
        x:625; y:108; width:28; height:28; radius:14; color:"transparent"; border.color:demoTheme.accent; border.width:2
        visible:movie.scene===3 && movie.local>3.6 && movie.local<4.4
      }
    }
    Text { x:120; y:520; text:movie.headings[movie.scene]; color:"#f1f3f6"; font.family:demoTheme.textFontFamily; font.pixelSize:44; font.weight:Font.DemiBold }
    Text { x:120; y:585; width:1040; text:movie.captions[movie.scene]; color:"#a7b1c0"; font.family:demoTheme.textFontFamily; font.pixelSize:22; wrapMode:Text.Wrap }
    Text { x:120; y:645; text:movie.scene===6 ? "github.com/Almichot-1/dynamic-island" : "Rendered demo · Sample data · No personal desktop capture"; color:movie.scene===6 ? demoTheme.accent : "#788494"; font.family:demoTheme.textFontFamily; font.pixelSize:16 }
    Row {
      x:1120; y:651; spacing:5
      Repeater { model:7; Rectangle { required property int index; width:8; height:4; radius:2; color:index===movie.scene ? demoTheme.accent : "#39414e" } }
    }
  }
  Timer {
    interval:40; repeat:true; running:true
    onTriggered: {
      if (movie.busy) return
      movie.busy=true
      canvas.grabToImage(function(result) {
        var name = String(movie.frame).padStart(5,"0")
        result.saveToFile(movie.output + "/frame-"+name+".png")
        movie.frame++
        movie.busy=false
        if (movie.frame>=1250) Qt.quit()
      })
    }
  }
}

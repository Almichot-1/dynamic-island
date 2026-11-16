import QtQuick
import QtQuick.Layouts
import "../../components"

Item {
  id: pill
  required property var agents
  readonly property var host: agents.host
  readonly property var theme: host.theme
  readonly property int activeCount: agents.sessions.filter(function(s) { return ["working", "thinking", "tool", "asking"].indexOf(s.state) !== -1 }).length
  readonly property int attentionCount: agents.sessions.filter(function(s) { return s.state === "asking" }).length
  opacity: agents.pillShown ? 1 : 0
  visible: opacity > 0.01
  Behavior on opacity { MotionAnimation { theme: pill.theme; pace: "fade"; curve: "fade" } }
  HoverHandler { enabled: pill.agents.pillShown; onHoveredChanged: pill.agents.hovered = hovered }
  Text {
    anchors.left: parent.left
    anchors.leftMargin: 14
    anchors.verticalCenter: parent.verticalCenter
    text: "  " + pill.activeCount
    color: pill.attentionCount ? pill.theme.system.orange : pill.theme.system.blue
    font.family: pill.theme.fontFamily
    font.pixelSize: 17
  }
  Text {
    anchors.right: parent.right
    anchors.rightMargin: 14
    anchors.verticalCenter: parent.verticalCenter
    text: pill.attentionCount ? "Needs you" : pill.agents.finished ? "Done" : "Working"
    color: pill.attentionCount ? pill.theme.system.orange : pill.theme.system.green
    font.family: pill.theme.textFontFamily
    font.pixelSize: 12
    font.bold: true
  }
}

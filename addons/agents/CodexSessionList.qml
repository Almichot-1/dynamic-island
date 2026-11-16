import QtQuick
import QtQuick.Layouts

ColumnLayout {
  id: list
  required property var agents
  required property var view
  Layout.fillWidth: true
  spacing: 8
  Text {
    Layout.fillWidth: true
    text: "Codex sessions · " + list.agents.sessions.length
    color: list.view.text
    font.family: list.view.host.theme.textFontFamily
    font.pixelSize: 15
    font.bold: true
  }
  Text {
    visible: list.agents.sessions.length === 0
    text: "No open local Codex sessions"
    color: list.view.textMuted
    font.family: list.view.host.theme.textFontFamily
    font.pixelSize: 12
  }
  Repeater {
    model: list.agents.sessions
    delegate: Rectangle {
      id: row
      required property var modelData
      Layout.fillWidth: true
      implicitHeight: 62
      radius: 12
      color: rowHover.hovered || activeFocus ? list.view.host.theme.wellHover : list.view.card
      border.color: list.view.edge
      activeFocusOnTab: true
      Accessible.role: Accessible.Button
      Accessible.name: "Open Codex session " + (modelData.label || modelData.id)
      Accessible.onPressAction: list.agents.openSession(row.modelData.id)
      Keys.onReturnPressed: list.agents.openSession(row.modelData.id)
      Keys.onEnterPressed: list.agents.openSession(row.modelData.id)
      Keys.onSpacePressed: list.agents.openSession(row.modelData.id)
      HoverHandler { id: rowHover; cursorShape: Qt.PointingHandCursor }
      TapHandler { onTapped: list.agents.openSession(row.modelData.id) }
      readonly property bool asking: modelData.state === "asking"
      readonly property bool working: ["working", "thinking", "tool"].indexOf(modelData.state) !== -1
      RowLayout {
        anchors.fill: parent
        anchors.margins: 10
        spacing: 10
        ColumnLayout {
          Layout.fillWidth: true
          spacing: 3
          Text {
            Layout.fillWidth: true
            text: row.modelData.label || "Codex"
            textFormat: Text.PlainText
            elide: Text.ElideRight
            color: list.view.text
            font.family: list.view.host.theme.textFontFamily
            font.pixelSize: 13
          }
          Text {
            Layout.fillWidth: true
            text: row.modelData.project + " · " + row.modelData.id.slice(-8)
            textFormat: Text.PlainText
            elide: Text.ElideRight
            color: list.view.textMuted
            font.family: list.view.host.theme.textFontFamily
            font.pixelSize: 11
          }
        }
        Text {
          text: row.asking ? (row.modelData.reason === "approval" ? "Approval needed" : "Input needed") : row.working ? "Working" : "Idle"
          color: row.asking ? list.view.host.theme.system.orange : row.working ? list.view.host.theme.system.green : list.view.textMuted
          font.family: list.view.host.theme.textFontFamily
          font.pixelSize: 12
          font.bold: row.asking
        }
      }
    }
  }
}

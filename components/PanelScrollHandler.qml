import QtQuick

// Keep scroll acceleration local to Island and leave system controls alone.
WheelHandler {
  id: handler
  required property var flickable
  property real speed: 2
  target: null
  acceptedDevices: PointerDevice.Mouse | PointerDevice.TouchPad
  blocking: true
  enabled: flickable.visible && flickable.contentHeight > flickable.height
  onWheel: function(event) {
    var delta = event.pixelDelta.y !== 0 ? event.pixelDelta.y : event.angleDelta.y / 2
    if (delta === 0) { event.accepted = false; return }
    flickable.cancelFlick()
    var top = flickable.originY
    var bottom = top + Math.max(0, flickable.contentHeight - flickable.height)
    flickable.contentY = Math.max(top, Math.min(bottom, flickable.contentY - delta * speed))
    event.accepted = true
  }
}

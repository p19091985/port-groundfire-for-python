extends Node

const FEATURE_LAN_DISCOVERY := "lan_discovery"
const FEATURE_UDP_TRANSPORT := "udp_transport"
const FEATURE_DEDICATED_SERVER_TOOLS := "dedicated_server_tools"
const FEATURE_BROWSER_SAFE_ONLINE := "browser_safe_online"


func is_web() -> bool:
	return OS.has_feature("web")


func is_desktop() -> bool:
	return not is_web()


func supports(feature_name: String) -> bool:
	match feature_name:
		FEATURE_BROWSER_SAFE_ONLINE:
			return true
		FEATURE_LAN_DISCOVERY, FEATURE_UDP_TRANSPORT, FEATURE_DEDICATED_SERVER_TOOLS:
			return is_desktop()
		_:
			return false


func visible_server_browser_tabs() -> PackedStringArray:
	var tabs := PackedStringArray(["Internet", "Favorites", "History"])
	if supports(FEATURE_LAN_DISCOVERY):
		tabs.append("LAN")
	return tabs


func hidden_web_features() -> PackedStringArray:
	if is_desktop():
		return PackedStringArray()
	return PackedStringArray([
		FEATURE_LAN_DISCOVERY,
		FEATURE_UDP_TRANSPORT,
		FEATURE_DEDICATED_SERVER_TOOLS,
	])

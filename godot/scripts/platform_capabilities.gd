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
	return supports_for_platform(feature_name, is_web())


static func supports_for_platform(feature_name: String, web_build: bool) -> bool:
	match feature_name:
		FEATURE_BROWSER_SAFE_ONLINE:
			return true
		FEATURE_LAN_DISCOVERY, FEATURE_UDP_TRANSPORT, FEATURE_DEDICATED_SERVER_TOOLS:
			return not web_build
		_:
			return false


func visible_server_browser_tabs() -> PackedStringArray:
	return visible_server_browser_tabs_for(is_web())


static func visible_server_browser_tabs_for(web_build: bool) -> PackedStringArray:
	var tabs := PackedStringArray(["Internet", "Favorites", "History"])
	if supports_for_platform(FEATURE_LAN_DISCOVERY, web_build):
		tabs.append("LAN")
	return tabs


func hidden_web_features() -> PackedStringArray:
	return hidden_features_for_platform(is_web())


static func hidden_features_for_platform(web_build: bool) -> PackedStringArray:
	if not web_build:
		return PackedStringArray()
	return PackedStringArray([
		FEATURE_LAN_DISCOVERY,
		FEATURE_UDP_TRANSPORT,
		FEATURE_DEDICATED_SERVER_TOOLS,
	])

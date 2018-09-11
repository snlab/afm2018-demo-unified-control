@load base/utils/strings
@load base/protocols/http/entities

module Trident;

export {
    global report: function(c: connection, key: string, value: string): int;
}

type Controller: record {
    url: string;
};

global controller_url: string;
const base_url = "%s/api/snlab/trident_server/v1/tridentkv?flow=%s&key=%s&value=%s";

function five_tuple(c: connection): string {
    local proto = get_port_transport_proto(c$id$orig_p);
    local sip: addr = c$id$orig_h;
    local dip: addr = c$id$resp_h;
    local sport: count = port_to_count(c$id$orig_p);
    local dport: count = port_to_count(c$id$resp_p);
    return cat("<", sip, ",", dip, ",", sport, ",", dport, ",", proto, ">");
}

function report(c: connection, key: string, value: string): int {
    local send = five_tuple(c);
    local url = fmt(base_url, controller_url, send, key, value);
    print send;
    print key;
    print value;
    when (local resp = ActiveHTTP::request([$url=url])) {
    }
    return 0;
}

event config(desc: Input::EventDescription, e: Input::Event, data: Controller) {
    controller_url = data$url;
}

event bro_init() {
    Input::add_event([$source="trident.conf", $name="trident",
                      $fields=Controller, $ev=config]);
}

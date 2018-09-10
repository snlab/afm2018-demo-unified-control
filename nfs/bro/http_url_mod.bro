@load base/protocols/http/main
@load base/utils/files
@load ./trident.bro

event http_header(c: connection, orig: bool, name: string, value: string) {
    if (/^[hH][oO][sS][tT]$/ in name) {
        Trident::report(c, "http_host", value);
        print "host: " + value;
    }
}

@load base/protocols/http/main
@load base/utils/files

event http_header(c: connection, orig: bool, name: string, value: string) {
    if (/^[hH][oO][sS][tT]$/ in name) {
        print "host: " + value;
    }
}

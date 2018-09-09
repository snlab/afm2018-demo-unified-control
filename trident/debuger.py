from napps.snlab.trident_server.trident.tridentlib import TridentServer
path = "napps/snlab/trident_server/trident/"

def test_lark(larkfile, progfile):
    trident = TridentServer()

    with open(progfile) as f:
        program = f.read()
        trident.set_ctx_controller("Fake")
        trident.submit(larkfile, program, debug=True)
        for t in trident.ctx.tables:
            print(t)

if __name__ == '__main__':
    test_lark(path + "example.lark", path + "example.tr")

from nccontainer.proto import tunnel_pb2


class Container:
    def __init__(self, dp_id, op_id, ack_from, ack_to, entry):
        """
        :param op_id: "10.0.0.1:3333:12345", the first part is ddp server address
        :param dp_id: "00:00:00:00:00:00:00:00"
        :param entry: b'openflowmsg'
        :param ack_from: "a&b|c"
        :param ack_to: "d&e|f"
        """
        self.op_id = op_id
        self.dp_id = dp_id
        self.entry = entry
        self.ack_from = ack_from
        self.ack_to = ack_to
        self.ack_from_list = self.__parse_ack(ack_from)
        self.ack_to_list = self.__parse_ack(ack_to)
        self.__update_state()

    def __parse_ack(self, logic_str):
        return [{cid:False for cid in and_str.split('&') if len(cid)>2}
                for and_str in logic_str.split('|')]

    def __str__(self):
        return "op_id='%s'; dpid='%s'; ack_from='%s'; ack_to='%s'" % (self.op_id, self.dp_id, self.ack_from, self.ack_to)

    def get_ack_to_address(self):
        # print(self.ack_to_list)
        # print(self.ack_from_list)
        # print(self.ack_to)
        # print(self.ack_from)
        addr_list = []
        if self.ack_to_list:
            for cid in self.ack_to_list[0]:
                a = cid.split(':')
                addr_list.append((a[0],int(a[1])))
        return addr_list

    def receive_ack(self, op_id):
        for and_map in self.ack_from_list:
            if op_id in and_map:
                and_map[op_id]=True
        self.__update_state()

    def __update_state(self):
        self.state = True if not self.ack_from_list \
            else any(all(and_map.values()) for and_map in self.ack_from_list)

    @classmethod
    def unpack(cls, data):
        proto = tunnel_pb2.Container()
        proto.ParseFromString(data)
        return Container(proto.dp_id, proto.op_id, proto.ack_from, proto.ack_to, proto.entry)

    def pack(self):
        proto = tunnel_pb2.Container()
        proto.dp_id = self.dp_id
        proto.op_id = self.op_id
        proto.ack_from = self.ack_from
        proto.ack_to = self.ack_to
        proto.entry = self.entry
        data = proto.SerializeToString()
        return data
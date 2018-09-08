#!/usr/bin/env python

class BuildDependency():
    class Switch():  # store switch route table
        id = 0
        flow = []
        bandwidth = []  # the rest bandwidth to other switch

        def __init__(self, i):
            self.id = i
            self.flow = []

        def findFlow(self, flowid):
            for i in self.flow:
                if i.flow_id == flowid:
                    return i
            return BuildDependency.Link(-1, -1, -1)

    class TLink():
        flow_add = []
        add_num = 0
        flow_minus = []
        minus_num = 0

    class Flow_head():  # store the begin of the flow
        id = 0
        head = 0

        def __init__(self, i, h):
            self.id = i
            self.head = h
            self.flow_add = []
            self.flow_minus = []

    class Link():
        flow_id = 0
        next_hop = 0
        bandwidth = 0

        def __init__(self, f, n, b):
            self.flow_id = f
            self.next_hop = n
            self.bandwidth = b

    class Configuration():
        configure_id = 0
        flow_id = 0
        switch_id = 0
        next_hop = 0
        operation = 'null'
        bandwidth = 0

        def __init__(self, cid, fid, swid, nhop, op, bw):
            self.configure_id = cid
            self.flow_id = fid
            self.switch_id = swid
            self.next_hop = nhop
            self.operation = op
            self.bandwidth = bw

    class pair():
        x = 0
        y = 0

        def __init__(self, x1, y1):
            self.x = x1
            self.y = y1

    configureList = []  # 2-D array , store configurations for all switches
    switchList = []
    linkList = []
    flowList = []
    ACK_from1 = {}
    ACK_to1 = {}
    ACK_from2 = {}
    ACK_to2 = {}
    ACK_from3 = {}
    ACK_to3 = {}
    leadTo = {}
    leadToTransitiveClosure = []

    configure_num = 200
    switch_num = 50

    def find_flow(self, id):
        for i in self.flowList:
            if i.id == id:
                return i
        return self.Flow_head(-1, -1)

    def blackholeDependency(self):
        # print(len(flowList))
        for i in range(0, len(self.flowList)):
            flowid = self.flowList[i].id
            hop = self.flowList[i].head

            while hop != -1:
                # print (hop)
                for j in range(0, len(self.configureList[hop])):
                    if self.configureList[hop][j].flow_id == flowid:
                        if self.configureList[hop][j].operation == 'modify':
                            nexthop = self.configureList[hop][j].next_hop
                            # print ('&&&' , flowid , hop , nexthop )
                            confid = self.configureList[hop][j].configure_id
                            # print(nexthop)
                            while True:
                                pd = False

                                for k in range(0, len(self.configureList[nexthop])):
                                    if self.configureList[nexthop][k].flow_id == flowid:
                                        if self.configureList[nexthop][k].operation == 'insert':
                                            nconfid = self.configureList[nexthop][k].configure_id
                                            self.ACK_from1[confid] = self.ACK_from1[confid] + ' & ' + str(nconfid)
                                            self.ACK_to1[nconfid] = self.ACK_to1[nconfid] + ' & ' + str(confid)
                                            nexthop = self.configureList[nexthop][k].next_hop
                                            pd = True
                                            break
                                if pd == False:
                                    break
                        break

                hop = self.switchList[hop].findFlow(flowid).next_hop
            hop = self.flowList[i].head
            # print("%%")
            # build the delete and modify dependency
            while hop != -1:
                # print(hop)
                # check if there are configuration of the flow in this switch
                for j in range(0, len(self.configureList[hop])):
                    if self.configureList[hop][j].flow_id == flowid:
                        if self.configureList[hop][j].operation == 'modify':
                            # print('###', flowid, hop, nexthop)
                            next_link = self.switchList[hop].findFlow(flowid)
                            confid = self.configureList[hop][j].configure_id
                            while True:
                                pd = False
                                for k in range(0, len(self.configureList[next_link.next_hop])):
                                    if self.configureList[next_link.next_hop][k].flow_id == flowid:
                                        if self.configureList[next_link.next_hop][k].operation == 'delete':
                                            pd = True
                                            nexthop = next_link.next_hop
                                            nconfid = self.configureList[nexthop][k].configure_id
                                            self.ACK_to1[confid] = self.ACK_to1[confid] + ' & ' + str(nconfid)
                                            self.ACK_from1[nconfid] = self.ACK_from1[nconfid] + ' & ' + str(confid)
                                            next_link = self.switchList[nexthop].findFlow(flowid)
                                        break
                                if pd == False:
                                    break
                        break

                hop = self.switchList[hop].findFlow(flowid).next_hop

            # build the delete and delete dependency
            hop = self.flowList[i].head
            # check if there are configuration of the flow in this switch
            for j in range(0, len(self.configureList[hop])):
                if self.configureList[hop][j].flow_id == flowid:
                    if self.configureList[hop][j].operation == 'delete':
                        next_link = self.switchList[hop].findFlow(flowid)
                        confid = self.configureList[hop][j].configure_id
                        while True:
                            pd = False
                            for k in range(0, len(self.configureList[next_link.next_flow])):
                                if self.configureList[hop][k].flow_id == flowid:
                                    if self.configureList[hop][k].operation == 'delete':
                                        pd = True
                                        nexthop = next_link.next_flow
                                        nconfid = self.configureList[nexthop][k].configure_id
                                        self.ACK_to1[nconfid] = self.ACK_to1[nconfid] + ' & ' + str(confid)
                                        self.ACK_from1[confid] = self.ACK_from1[confid] + ' & ' + str(nconfid)
                                        next_link = self.switchList[nexthop].findFlow(flowid)
                                break
                            if pd == False:
                                break
                break

        # build the insert and insert dependency
        newFlow = {}
        for sw in range(0, len(self.configureList)):
            for i in self.configureList[sw]:
                if i.operation == 'insert' and self.find_flow(i.flow_id).id == -1:
                    if not i.flow_id in newFlow.keys():
                        newFlow[i.flow_id] = []
                    newFlow[i.flow_id].append(i.next_hop)

        # for ii in newFlow[3]:
        # print('*' , ii)
        for sw in range(0, len(self.configureList)):
            for i in self.configureList[sw]:
                if i.operation == 'insert' and self.find_flow(i.flow_id).id == -1:
                    # print('^' , i.switch_id)
                    if i.flow_id in newFlow.keys() and not i.switch_id in newFlow[i.flow_id]:
                        for sww in range(0, len(self.configureList)):
                            for j in self.configureList[sww]:
                                if j.operation == 'insert' and j.flow_id == i.flow_id and j != i:
                                    self.ACK_from1[i.configure_id] = self.ACK_from1[i.configure_id] + ' & ' + str(
                                        j.configure_id)
                                    self.ACK_to1[j.configure_id] = self.ACK_to1[j.configure_id] + ' & ' + str(
                                        i.configure_id)

    def loopDependency(self):
        for i in range(0, len(self.flowList)):
            flowid = self.flowList[i].id
            hop = self.flowList[i].head
            conflist = []
            while hop != -1:
                # check if there are configuration of the flow in this switch
                for j in range(0, len(self.configureList[hop])):
                    if self.configureList[hop][j].flow_id == flowid:
                        if self.configureList[hop][j].operation == 'modify':
                            next_link = self.switchList[hop].findFlow(flowid)
                            confid = self.configureList[hop][j].configure_id
                            conflist.append(confid)
                            for k in range(0, len(self.configureList[next_link.next_hop])):
                                if self.configureList[hop][k].flow_id == flowid:
                                    if self.configureList[hop][k].operation == 'modify' and self.configureList[hop][
                                        k].next_hop in conflist:
                                        nexthop = next_link.next_hop
                                        nconfid = self.configureList[nexthop][k].configure_id
                                        self.ACK_to2[nconfid] = self.ACK_to2[nconfid] + ' & ' + str(confid)
                                        self.ACK_from2[confid] = self.ACK_from2[confid] + ' & ' + str(nconfid)
                                    break
                        break
                hop = self.switchList[hop].findFlow(flowid).next_hop

    congestionConfigure = []
    linkFlow_add = {}
    linkFlow_minus = {}

    def findCongestionConfigure(self):
        # modify and delete
        for i in range(0, len(self.flowList)):
            flowid = self.flowList[i].id
            hop = self.flowList[i].head
            for j in range(0, len(self.configureList)):
                if self.configureList[j].flow_id == flowid and self.configureList[j].switch_id == hop:
                    self.congestionConfigure.append(self.configureList[j])
                    # linkFlow_add[configureList[j].flow_id] = []
                    # linkFlow_minus[configureList[j].flow_id] = []
        # insert
        insertFlowId = []
        insertFlow = {}

        for i in range(0, len(self.configureList)):
            if self.configureList[i].operation == 'insert':
                if not self.configureList[i].flow_id in insertFlowId:
                    insertFlowId.append(self.configureList[i].flow_id)
                    insertFlow[self.configureList[i].flow_id] = []
                insertFlow[self.configureList[i].flow_id].appaend(self.configureList[i].next_hop)
        for i in insertFlow:
            for j in range(0, len(self.configureList)):
                if self.configureList[j].operation == 'insert':
                    if self.configureList[j].flow_id == insertFlowId[i] and not self.configureList[j].switch_id in \
                            insertFlow[i]:
                        self.congestionConfigure.append(self.configureList[j])
                        # linkFlow_add[configureList[j].flow_id] = []
                        # linkFlow_minus[configureList[j].flow_id] = []

        for i in self.congestionConfigure:
            hop = i.switch_id
            flow = i.flow
            while hop != -1:
                for j in self.configureList:
                    if j.flow_id == flow and j.switch_id == hop:
                        self.linkFlow_minus[self.pair(hop, hop.next_hop)].append(j)
                        break
                hop = hop.next_hop
            hop = i.switch_id
            while hop != -1:
                for j in self.configureList:
                    if j.flow_id == flow and j.switch_id == hop:
                        self.linkFlow_minus[self.pair(hop, j.next_hop)].append(j)
                        hop = j.next_hop
                        break

    def findFeasibleCombination(self, i, j, req, k, c, combine):
        if k == len(self.linkList[i][j].flow_minus):
            return
        if req <= 0:
            combine += c - '&' + '|'
            return
        self.findFeasibleCombination(i, j, req - self.linkList[i][j].minus_num[k].bandwidth, k + 1,
                                     c + '&' + self.linkList[i][j].minus_num[k].configure_num, combine)
        self.findFeasibleCombination(i, j, req, k + 1, c, combine)

    def leadToDependency(self):
        for i in range(0, len(self.configureList)):
            c = []
            for j in range(0, len(self.configureList)):
                c.append(0)
                self.leadToTransitiveClosure.append(c)

        for i in range(0, self.configure_num):
            for j in range(0, self.configure_num):
                for k1 in range(0, len(self.linkList[i][j].flow_add)):
                    for k2 in range(0, len(self.linkList[i][j].flow_add)):
                        if self.linkList[i][j].flow_add[k1].bandwidth < self.linkList[i][j].flow_minus[k2].bandwidth:
                            self.leadTo[self.linkList[i][j].flow_add[k1].configure_id].append(
                                self.linkList[i][j].flow_minus[k1].configure_id)
                            self.leadToTransitiveClosure[self.linkList[i][j].flow_add[k1].configure_id][
                                self.linkList[i][j].flow_minus[k1].configure_id] = 1
        for k in range(0, len(self.configureList)):
            for i in range(0, len(self.configureList)):
                for j in range(0, len(self.configureList)):
                    self.leadToTransitiveClosure[i][j] |= self.leadToTransitiveClosure[i][k] & \
                                                          self.leadToTransitiveClosure[k][j]

    def handleSEC(self, i, j, EC, SEC, k, avbw, comebine):
        if k == len(SEC) - 1:
            addn = 0
            for i1 in EC:
                addn += self.linkList[i][j].flow_add[i1].bandwidth
            avbw2 = avbw - addn
            self.findFeasibleCombination(i, j, -avbw2, '', comebine)

            return
        self.handleSEC(i, j, EC, SEC, k + 1, avbw, comebine)
        SEC.append(EC[k])
        self.handleSEC(i, j, EC, SEC, k + 1, avbw, comebine)
        SEC.pop()

    def congestionDependency(self):
        for i in range(0, self.configure_num):
            for j in range(0, self.configure_num):
                if self.linkList[i][j].add_num > self.linkList[i][j].minus_num + self.switchList[i].bandwidth[j]:
                    return False
                if len(self.linkList[i][j].flow_add) == 1:
                    comebine = ''
                    self.findFeasibleCombination(i, j, self.linkList[i][j].add_num - self.switchList[i].bandwidth[j],
                                                 '', comebine)
                    self.ACK_from3[self.linkList[i][j].flow_add[0].configure_id] = comebine
                if len(self.linkList[i][j].flow_add) > 1:
                    for k in range(0, len(self.linkList[i][j].flow_add)):
                        avbw = self.switchList[i].bandwidth[j]
                        EC = []
                        for k1 in range(0, len(self.linkList[i][j].flow_add)):
                            if k != k1 and self.leadToTransitiveClosure[self.linkList[i][j].flow_add[k].configure_id][
                                self.linkList[i][j].flow_add[k1].configure_id] == 1:
                                avbw -= self.linkList[i][j].flow_add[k1].bandwidth
                            if k != k1 and self.leadToTransitiveClosure[self.linkList[i][j].flow_add[k].configure_id][
                                self.linkList[i][j].flow_add[k1].configure_id] == 0 and \
                                            self.leadToTransitiveClosure[self.linkList[i][j].flow_add[k1].configure_id][
                                                self.linkList[i][j].flow_add[k].configure_id] == 0:
                                EC.append(k1)
                        comebine = ''
                        self.findFeasibleCombination(i, j, -avbw, '', comebine)
                        self.handleSEC(i, j, EC, [], 0, avbw, comebine)
                        self.ACK_from3[self.linkList[i][j].flow_add[k].configure_id] = comebine

    def __init__(self):
        global containerList
        fp = open('/home/ubuntu/Desktop/nc/nccontainer/test/switch.txt', 'r')
        reads = fp.readlines()
        # print(len(reads))
        for i in range(0, self.switch_num):
            content = reads[i].split()
            self.switchList.append(self.Switch(i))
            self.switchList[i].id = i

            for j in range(0, int(content[0])):  # get routing table
                self.switchList[i].flow.append(self.Link(int(content[j * 3 + 1]), int(content[j * 3 + 2]),
                                                         int(content[j * 3 + 3])))  # (-1 , -1 , -1) means null

        for i in range(0, self.switch_num):
            # print(i)
            content = reads[self.switch_num + i].split()
            # print(len(content))
            self.switchList[i].id = i
            for j in range(0, self.switch_num):  # routing table
                # print(j ,int(content[j]) )
                self.switchList[i].bandwidth.append(int(content[j]))  # -1 means no link
            for j in range(0, len(self.switchList[i].flow)):
                self.switchList[i].bandwidth[self.switchList[i].flow[j].next_hop] -= self.switchList[i].flow[
                    j].bandwidth
                self.switchList[self.switchList[i].flow[j].next_hop].bandwidth[i] -= self.switchList[i].flow[
                    j].bandwidth

        fp = open('/home/ubuntu/Desktop/nc/nccontainer/test/flow.txt', 'r')
        reads = fp.readlines()
        for fileline in reads:
            content = fileline.split()
            self.flowList.append(self.Flow_head(int(content[0]), int(content[1])))
        fp.close()

        for i in range(0, self.switch_num):
            # s = Switch(i)
            # switchList.append(s)
            s = []
            self.configureList.append(s)

            l = []
            for j in range(0, self.switch_num):
                l.append(self.TLink())
            self.linkList.append(l)

        fp = open('/home/ubuntu/Desktop/nc/nccontainer/test/configure.txt', 'r')
        reads = fp.readlines()

        countc = 0

        for fileline in reads:
            content = fileline.split()
            # configuration_id , flow_id , switch_id , next_hop , operation , bandwidth
            c = self.Configuration(countc, int(content[0]), int(content[1]), int(content[2]), content[3],
                                   int(content[4]))
            self.ACK_from1[countc] = ''
            self.ACK_from2[countc] = ''
            self.ACK_from3[countc] = ''
            self.ACK_to1[countc] = ''
            self.ACK_to2[countc] = ''
            self.ACK_to3[countc] = ''
            if content[3] == 'modify':
                for k in range(0, len(self.configureList[int(content[1])])):
                    if self.configureList[int(content[1])][k].flow_id == int(content[0]):
                        self.linkList[int(content[1])][
                            self.configureList[int(content[1])][k].next_hop].flow_minus.append(c)
                        self.linkList[int(content[1])][
                            self.configureList[int(content[1])][k].next_hop].minus_num += int(
                            content[4])
                        break

                self.linkList[int(content[1])][int(content[2])].flow_add.append(c)
                self.linkList[int(content[1])][int(content[2])].add_num += int(content[4])
            if content[3] == 'insert':
                self.linkList[int(content[1])][int(content[2])].flow_add.append(c)
                self.linkList[int(content[1])][int(content[2])].add_num += int(content[4])
            if content[3] == 'delete':
                for k in range(0, len(self.configureList[int(content[1])])):
                    if self.configureList[int(content[1])][k].flow_id == int(content[0]):
                        self.linkList[int(content[1])][
                            self.configureList[int(content[1])][k].next_hop].flow_minus.append(c)
                        self.linkList[int(content[1])][
                            self.configureList[int(content[1])][k].next_hop].minus_num += int(
                            content[4])
                        break

            countc = countc + 1
            self.configureList[int(content[1])].append(c)
        fp.close()
        self.blackholeDependency()
        self.loopDependency()
        self.congestionDependency()

        for i in range(len(self.configureList)):
            for j in self.configureList[i]:
                af1 = ncctunnel.nccontainer()
                _n = i + 1
                if _n < 16:
                    af1.switch = "00:00:00:00:00:0" + str(hex(_n))[2:]
                else:
                    af1.switch = "00:00:00:00:00:" + str(hex(_n))[2:]
                af1.op_id = str(j.configure_id)
                af1.instruction = j.operation
                if len(self.ACK_from1[j.configure_id]) != 0:
                    self.ACK_from1[j.configure_id] = self.ACK_from1[j.configure_id][
                                                     2:len(self.ACK_from1[j.configure_id])]
                if len(self.ACK_from2[j.configure_id]) != 0:
                    self.ACK_from2[j.configure_id] = self.ACK_from2[j.configure_id][
                                                     2:len(self.ACK_from2[j.configure_id])]
                if len(self.ACK_from3[j.configure_id]) != 0:
                    self.ACK_from3[j.configure_id] = self.ACK_from3[j.configure_id][
                                                     2:len(self.ACK_from2[j.configure_id])]

                if len(self.ACK_to1[j.configure_id]) != 0:
                    self.ACK_to1[j.configure_id] = self.ACK_to1[j.configure_id][2:len(self.ACK_from1[j.configure_id])]
                if len(self.ACK_to1[j.configure_id]) != 0:
                    self.ACK_to2[j.configure_id] = self.ACK_to2[j.configure_id][2:len(self.ACK_from1[j.configure_id])]
                if len(self.ACK_to1[j.configure_id]) != 0:
                    self.ACK_to3[j.configure_id] = self.ACK_to3[j.configure_id][2:len(self.ACK_from1[j.configure_id])]

                af1.ack_from = self.ACK_from1[j.configure_id] + ' + ' + self.ACK_from2[j.configure_id] + ' + ' + \
                               self.ACK_from3[j.configure_id]
                af1.ack_to = self.ACK_to1[j.configure_id] + ' + ' + self.ACK_to2[j.configure_id] + ' + ' + self.ACK_to3[
                    j.configure_id]
                containerList.append(af1)

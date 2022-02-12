import random
import matplotlib.pyplot as plt
import numpy as np

'''
num_clients = 80
packets_per_client = 10
num_load_balancers = 2
num_servers = 4
processing_time = 0.005 # time per packet
'''

# Packet generation variables
num_flows = 150
mean_flow_size = 15
flow_size_stdev = 2
max_flow_duration = 0.05
# Num clients, load balancers, servers
num_clients = 32
num_load_balancers = 4
num_servers = 8
# Server processing time, time per packet
processing_time = 0.004

#value for powers of x choices
powers_of_x_value = 3

#whether or not a load balancer drops
LOAD_BALANCER_DROPS = False



assignment_methods = ["RandomAssignment", "ConsistentHashing", "PowersOfTwoNoMemory", "PowersOfTwoWithMemory", "PowersOfXWithMemory"]
powers_of_x = [2, 4, 8]

#class defining a client/host
class Client:
	def __init__(self, address):
		self.id = address

#class defining the load balancer
class LoadBalancer:
	def __init__(self, address):
		self.id = address
		self.connection_table = {}
		
	def __repr__(self):
		return "Load Balancer id: " + str(self.id)	

#class defining a backend server clients are making requests to 
class Server:
	def __init__(self, address):
		self.id = address
		self.packet_history = []

	def add_packet(self, packet):
		self.packet_history.append(packet)

	def clear_packets(self):
		self.packet_history.clear()

	#calculate the amount of time until the queue is theoretically free
	def get_load(self, current_time):
		if len(self.packet_history) == 0:
			return 0
		TTF = 0
		t = 0
		i = 0
		while t < current_time:
			if i >= len(self.packet_history):
				break
			packet_i = self.packet_history[i]
			if packet_i.time_sent > current_time:
				break
			if TTF > 0:
				TTF -= (packet_i.time_sent - t)
				if TTF < 0:
					TTF = 0
			TTF += processing_time
			t = packet_i.time_sent
			i += 1
		TTF -= (current_time - t)
		if TTF < 0:
			TTF = 0
		return TTF

	def __repr__(self):
		string = ""
		for packet in self.packet_history:
			string += str(round(packet.time_sent,3)) + " "
		return "Server id: " + str(self.id) +"\n" + "Packet arrival times: " + string

#class defining a packet
class Packet:
	def __init__(self, clientid, port_number,time_sent):
		self.clientid = clientid
		self.port_num = port_number
		self.time_sent = time_sent

	def __repr__(self):
		return "Packet from client: " + str(self.clientid) + "at port: " + str(self.port_num) +  " @time: " + str(round(self.time_sent,3))


	def run_consistency_check(servers):
	perFlowConsistent = True
	for server in servers:
		for otherServer in servers:
			if server.id != otherServer.id:
				for packet in server.packet_history:
					if (packet.clientid, packet.port_num) in [(pckt.clientid, pckt.port_num) for pckt in otherServer.packet_history]:
						perFlowConsistent = False
						break

	if perFlowConsistent:
		print("Per-Flow Consistency Maintained")
	else:
		print("Per-Flow Consistency Not Maintained")



def run_simulation(assignment_method):
	print("running simulation for " + assignment_method)

	# Initialization Steps
	packets = []
	for i in range(num_flows):
		num_packets_in_flow = int(np.random.normal(mean_flow_size, flow_size_stdev))
		client_of_flow = random.randint(0, num_clients-1) # client id -- random????
		time_of_flow = random.random()
		port_number = random.randint(1024, 65536)
		for j in range(num_packets_in_flow):
			time_of_packet = time_of_flow + (random.random() * (max_flow_duration) - max_flow_duration / 2) # why ????
			packet = Packet(client_of_flow, port_number, time_of_packet)
			packets.append(packet)
	packets.sort(key=lambda x: x.time_sent, reverse=False)

	load_balancers = []
	for i in range(num_load_balancers):
		load_balancer = LoadBalancer(i)
		load_balancers.append(load_balancer)

	servers = []
	for i in range(num_servers):
		server = Server(i)
		servers.append(server)

	# Main Simulation Processing Loop
	for i in range(len(packets)):
		packet = packets[i]

		if LOAD_BALANCER_DROPS: 
			if i < len(packets)/2:
				lb_id = packet.clientid % num_load_balancers
			else: #last load balancer "goes down"
				lb_id = packet.clientid % (num_load_balancers - 1)
		else:
			lb_id = packet.clientid % num_load_balancers #???????? 

		load_balancer = load_balancers[lb_id] # choose the balancer randomly????
		switcher = {
			"RandomAssignment": load_balancer.assign_server_random,  # No per-flow consistency :(
			"ConsistentHashing": load_balancer.assign_server_hashing, # Per-flow consistency :)
			"PowersOfTwoNoMemory": load_balancer.assign_server_power_of_2_choices_no_memory, # No Per-flow consistency :( + Congestion control :)
			"PowersOfTwoWithMemory": load_balancer.assign_server_power_of_2_choices_with_memory, # Per-flow consistency :) + Congestion control :) 
			"PowersOfXWithMemory": load_balancer.assign_server_power_of_x_choices_with_memory # Per-flow consistency :) + Congestion control :) 
		}
		func = switcher.get(assignment_method, lambda: "Invalid assignment method")
		server_id = func(packet, servers, powers_of_x_value)
		server = servers[server_id]
		server.add_packet(packet)
		#print("Load Balancer " + str(lb_id) + " sent packet from client " + str(packet.clientid) + " to server " + str(server_id))

	run_load_plotter(servers, assignment_method)
	run_mean_and_stdev_plotter(servers, assignment_method)
	run_consistency_check(servers)
	print()

for method in assignment_methods:
	run_simulation(method)

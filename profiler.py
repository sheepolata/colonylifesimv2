import numpy as np

class Profiler(object):
	"""docstring for Profiler"""
	def __init__(self):
		super(Profiler, self).__init__()
		
		self.time_dict = {}

	def add_time_record(self, key, value):
		try:
			self.time_dict[key].append(value)
		except Exception as e:
			self.time_dict[key] = [value]

	def display_time_infos(self):
		print("###### PROFILER INFORMATION")
		for k in self.time_dict.keys():
			_avg = np.mean(self.time_dict[k])
			_min = min(self.time_dict[k])
			_max = max(self.time_dict[k])

			print("########### {}\n\t\t~{} ms / [{} ms; {} ms]\n".format(k, round(_avg, 5)*1000, round(_min, 5)*1000, round(_max, 5)*1000))

profiler = Profiler()
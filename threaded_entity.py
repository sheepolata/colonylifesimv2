import life
import threading

class ThreadedEntity(threading.Thread):
	def __init__(self, simu, tile, name):
		self.entity = life.Entity(simu, tile, name)
		self.paused = False

		self.over = False

	def run(self):
		while not self.over:
			if not self.paused:
				self.entity.update()

	def pause(self):
		self.paused = not self.paused

	def finish(self):
		self.over = True
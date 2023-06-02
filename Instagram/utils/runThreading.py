'''
Foodvocate: Multithreading
Author: Meng-Chieh Liu
Github: https://github.com/MengChiehLiu
Date: 2023/5/22
'''

from threading import Thread

def runThreading(my_queue, func, thread_amount):
    class Worker(Thread):
        def __init__(self, queue):
            Thread.__init__(self)
            self.queue = queue

        def run(self):
            while self.queue.qsize() > 0:
                element = self.queue.get()
                if isinstance(element, tuple):
                    func(*element)
                else:
                    func(element)
    
    # workers start working
    workers = [Worker(my_queue) for _ in range(thread_amount)]
    for worker in workers:
        worker.start()
    for worker in workers:
        worker.join()
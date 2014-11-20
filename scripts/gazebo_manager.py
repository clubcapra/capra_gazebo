import os
import subprocess
import rosnode
import tornado.websocket
import tornado.web
import tornado.httpserver
import time
import threading
import rospkg
from os import listdir
from os.path import isfile, join


MAX_INSTANCES = 4
PORTS = range(1337, 1337 + 2 * MAX_INSTANCES)


class Instance:
    core_port = 0
    gazebo_port = 0
    world = ""
    proc = None

    def __init__(self, core_port, gazebo_port, world):
        self.core_port = core_port
        self.gazebo_port = gazebo_port
        self.world = world
        
    def _setenv(self):
        os.environ["ROS_MASTER_URI"] = "http://localhost:%d" % self.core_port
        os.environ["GAZEBO_MASTER_URI"] = "http://localhost:%d" % self.gazebo_port

    def run(self):
        self._setenv()
        cmd = "roslaunch -p %d capra_gazebo Gazebo_world_arg.launch world:=%s" % (self.core_port, self.world)
        self.proc = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE)

    def kill(self):   
        self._setenv()
        rosnode.kill_nodes(['gazebo'])
        time.sleep(2)
        self.proc.terminate()


class InstanceManager(tornado.websocket.WebSocketHandler):
    instances = {}
    create_lock = threading.Lock()

    def get_free_ports(self):
        ports = PORTS[:]
        for i in self.instances.values():
            ports.remove(i.core_port)
            ports.remove(i.gazebo_port)
        return ports[:2]

    def list(self, m):
        r = ""
        for name, instance in self.instances.items():
            r += name + "\n"
        self.write_message(r.strip())

    def list_worlds(self, m):
        rospack = rospkg.RosPack()
        path = rospack.get_path("capra_gazebo") + "/worlds"
        r = ""
        for w in [f[:-len(".world")] for f in listdir(path) if f.endswith(".world")]:
            r += w + "\n"
        self.write_message(r.strip())

    def create(self, m):
        self.create_lock.acquire()
        if len(m) == 3:
            if len(self.instances) < MAX_INSTANCES:
                name = m[1]
                world = m[2]
                if not name in self.instances:
                    p1, p2 = self.get_free_ports()
                    self.instances[name] = Instance(int(p1), int(p2), world)
                    self.instances[name].run()
                    self.write_message("%d %d" % (p1, p2))
                    self.create_lock.release()
                    return
        self.create_lock.release()
        self.write_message("Err")

    def kill(self, m):
        if len(m) == 2:
            if m[1] in self.instances:
                self.instances[m[1]].kill()
                del(self.instances[m[1]])
                self.write_message("OK")

    def on_message(self, msg):
        actions = {'list': self.list,
                   'list_worlds': self.list_worlds,
                   'create': self.create,
                   'kill': self.kill}
        m = msg.split()
        if len(m) > 0 and m[0] in actions:
            actions[m[0]](m)

    def on_close(self):
        print "WebSocket closed"

    def open(self):
        print "WebSocket opened"

if __name__ == "__main__":
    application = tornado.web.Application([(r'/ws', InstanceManager),])
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(8888)
    tornado.ioloop.IOLoop.instance().start()

from dataclasses import dataclass
import dataclasses
import os
import json
import heapq
import time

from threading import Lock

def mutex(*args_, **kwargs_):
    def w1(func):
        def wrapper(self, *args, **kwargs):
            with kwargs_["lock"]:
                val = func(self, *args, **kwargs)
            return val
        return wrapper
    return w1

@dataclass
class MessageData:
    expiry: int
    message_id: int
    url: str
    author: int
    message: str

PATH = "data.json"

datalock = Lock()

class DataclassEncoder(json.JSONEncoder):
    def default(self, o):
        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)
        return super().default(o)

class MessageDatabase:
    data: dict[int, MessageData] # message id -> message data
    heap: list[tuple[int, int]] # (expiry, message id)

    def __init__(self) -> None:
        with datalock:
            if not os.path.exists(PATH):
                self.data, self.heap = dict(), []
            else:
                with open(PATH) as f:
                    try:
                        [data, self.heap] = json.loads(f.read())
                        self.data = dict()
                        for k, v in data.items():
                            self.data[int(k)] = MessageData(
                                int(v["expiry"]),
                                int(v["message_id"]),
                                v["url"],
                                int(v["author"]),
                                v["message"],
                            )
                    except:
                        self.data, self.heap = dict(), []
            heapq.heapify(self.heap)
            self.clean()
    
    def save(self):
        with open(PATH, "w") as f:
            f.write(json.dumps([self.data, self.heap], cls=DataclassEncoder))
    
    def clean(self):
        cur_time = int(time.time())
        while self.heap and self.heap[0][0] < cur_time:
            del self.data[self.heap[0][1]]
            heapq.heappop(self.heap)
        self.save()
    
    @mutex(lock=datalock)
    def add(self, m: MessageData) -> None:
        heapq.heappush(self.heap, (m.expiry, m.message_id))
        self.data[m.message_id] = m
        self.clean()
    
    @mutex(lock=datalock)
    def get(self, message_id: int) -> MessageData | None:
        if not (message_id in self.data): return None
        data = self.data[message_id]
        if int(time.time()) >= data.expiry: return None
        return data
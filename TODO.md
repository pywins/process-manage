# TODO LIST

## The function of the missing

- [x] config support
- [x] pid storage to file
- [x] graceful kill child process
- [x] graceful stop child process while master process shutdown
- [x] maybe we should reconstruct the logger module
- [x] encapsulate fork subprocess (more than one call `Process(target=o.start)` )
- [x] what if i want multiprocess run `putworker` and multiprocess run `otherworker`
- [x] StopIterator while yield repeat call next(`now no the question, because of queue used.`)

## Issue


- log module issue  format is wrong
```
    2018-04-05 14:06:18 [45739] [DEBUG] Traceback (most recent call last): at logger.py(34)
    2018-04-05 14:06:18 [45739] [DEBUG]   File "/Users/william/python/process-manage/main.py", line 18, in <module> at logger.py(34)
    2018-04-05 14:06:18 [45739] [DEBUG] app.run(config) at logger.py(34)
    2018-04-05 14:06:18 [45739] [DEBUG]   File "/Users/william/python/process-manage/app/application.py", line 34, in run at logger.py(34)
    2018-04-05 14:06:18 [45739] [DEBUG] self.start_workers(workers_dir) at logger.py(34)
    2018-04-05 14:06:18 [45739] [DEBUG]   File "/Users/william/python/process-manage/app/application.py", line 58, in start_workers at logger.py(34)
    2018-04-05 14:06:18 [45739] [DEBUG] module = __import__(module_name, globals(), locals()) at logger.py(34)
    2018-04-05 14:06:18 [45739] [DEBUG] ModuleNotFoundError at logger.py(34)
    2018-04-05 14:06:18 [45739] [DEBUG] : at logger.py(34)
    2018-04-05 14:06:18 [45739] [DEBUG] No module named 'PutWorker' at logger.py(34)

   we need:
    2018-04-05 14:06:18 [45739] [DEBUG] Traceback (most recent call last): at logger.py(34)
                                        File "/Users/william/python/process-manage/main.py", line 18, in <module> at logger.py(34)
                                        ......
                                        No module named 'PutWorker' at logger.py(34)

```

- [ERROR] Handle SIGCHLD failed.[Errno 10] No child processes. at application.py(141)

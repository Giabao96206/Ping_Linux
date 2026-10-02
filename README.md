# PySudo Terminal

Một project Python mang tính giáo dục, tạo terminal mini có cách dùng gần giống `sudo`.

> **Quan trọng:** Project này **không tự tạo cơ chế nâng quyền root**. Nó gọi `sudo` của Linux khi người dùng dùng lệnh `sudo ...`. Đây là lựa chọn an toàn hơn so với biến một script Python thành SUID root.

## 1. Tính năng

- REPL terminal mini.
- Chạy command bình thường.
- `sudo <command>` để chạy command qua sudo hệ thống.
- `shell <command>` hỗ trợ pipe/redirection thông qua bash.
- `root-shell` mở một shell bằng sudo.
- `cd`, `pwd`, `history`, `id`, `clear`, `help`.
- Chế độ chạy một lần bằng `--once`.

## 2. Cài đặt trên Raspberry Pi / Linux

```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv sudo

cd ~/pysudo-project
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

Kiểm tra:

```bash
pysudo --help
```

## 3. Chạy terminal

```bash
pysudo
```

Ví dụ:

```text
pysudo:~$ id
pysudo:~$ ls -la
pysudo:~$ sudo ls -la /root
pysudo:~$ sudo apt update
pysudo:~$ root-shell
root@raspberrypi:~# id
```

## 4. Chạy một command

```bash
pysudo --once "id"
pysudo --once "ls -la /tmp"
pysudo --sudo --once "id"
pysudo --sudo --once "ls -la /root"
```

Pipe/redirection:

```bash
pysudo --shell --once "ps aux | grep python"
pysudo --sudo --shell --once "cat /etc/shadow | head"
```

## 5. Vì sao không dùng SUID cho file Python?

Nếu đặt SUID root lên một executable mà cuối cùng chạy một Python interpreter, bạn đang tạo ra một đường dẫn rất nguy hiểm để cấp quyền root cho cả runtime Python và môi trường của nó. `sudo` thực tế có nhiều cơ chế bảo vệ, kiểm soát môi trường và xử lý authentication/UID/GID.

Vì thế kiến trúc của project này là:

```text
             PySudo (Python)
                    |
           parse command / REPL
                    |
        +-----------+-----------+
        |                       |
      normal                  sudo
        |                       |
   subprocess()            /usr/bin/sudo
                                |
                       authentication
                                |
                        UID/GID transition
                                |
                          target program
```

## 6. Cấu trúc project

```text
pysudo-project/
├── pyproject.toml
├── README.md
├── pysudo/
│   ├── __init__.py
│   ├── cli.py
│   └── core.py
└── tests/
    └── test_core.py
```

## 7. Chạy test

```bash
python3 -m pytest
```

Nếu chưa có pytest:

```bash
pip install pytest
python3 -m pytest
```

## 8. Hướng phát triển tiếp theo

Có thể phát triển project thành một terminal Linux mini hoàn chỉnh hơn với:

1. Password/session cache giống sudo.
2. File cấu hình quyền kiểu `/etc/pysudoers`.
3. Whitelist command.
4. Audit log.
5. Timeout cho phiên nâng quyền.
6. Hỗ trợ job control/background (`&`, `jobs`, `fg`).
7. Tab completion.
8. PTY đầy đủ cho chương trình tương tác.
9. Một helper native C/Rust rất nhỏ để xử lý phần privilege boundary thay vì SUID Python.

"""
AutoTyHub V5 TURBO - Phiên Bản Tối Ưu Lợi Nhuận (Latency Compensated)
Chế Độ: PRE-CRASH -100ms | AUTO POST 0s | Server Sync | Precision Sleep
"""
import sys, asyncio, os, subprocess, time, random, json, base64, logging, statistics
from datetime import datetime
from collections import deque

if sys.platform == 'win32':
    os.system('chcp 65001 > nul')
    sys.stdout.reconfigure(encoding='utf-8')

for n in ["urllib3","aiohttp","requests"]:
    logging.getLogger(n).setLevel(logging.CRITICAL)
logging.basicConfig(level=logging.CRITICAL)
import warnings; warnings.filterwarnings("ignore")

def _install():
    pkgs = {"aiohttp":"aiohttp","colorama":"colorama"}
    miss = [v for k,v in pkgs.items() if not _try(k)]
    if miss:
        subprocess.check_call([sys.executable,"-m","pip","install"]+miss,
                              stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        os.execv(sys.executable,[sys.executable]+sys.argv)
def _try(n):
    try: __import__(n); return True
    except: return False
_install()

import aiohttp
from colorama import init as ci, Fore, Back, Style
ci(autoreset=True)

class M:
    R=Fore.LIGHTRED_EX; G=Fore.LIGHTGREEN_EX; Y=Fore.LIGHTYELLOW_EX
    B=Fore.LIGHTBLUE_EX; P=Fore.LIGHTMAGENTA_EX; C=Fore.LIGHTCYAN_EX
    W=Fore.LIGHTWHITE_EX; X=Style.RESET_ALL; D=Style.BRIGHT
    GR=Fore.LIGHTBLACK_EX
    # Debug colors
    DBG_API  = Fore.CYAN           # API request/response
    DBG_JWT  = Fore.MAGENTA        # JWT decode
    DBG_TIME = Fore.YELLOW         # Timing
    DBG_RES  = Fore.LIGHTGREEN_EX  # Result
    DBG_SEP  = Fore.LIGHTBLACK_EX  # Separator
    DBG_ERR  = Fore.LIGHTRED_EX    # Debug error
    DBG_SYS  = Fore.LIGHTBLUE_EX   # System/sync

def fnum(n): return f"{int(n):,}" if isinstance(n,(int,float)) and float(n).is_integer() else f"{n}"
def fmoney(n): return f"{fnum(n)} VNĐ"
def ts(): return datetime.now().strftime("%H:%M:%S")

# ═══ CẤU HÌNH V5 ═══
SETTINGS_FILE = "tyhub_settings_v5.json"
DATA_FILE = "data.txt"
INIT_DATA_FILE = "tyhub_init_data.txt"
BASE_URL = "https://typhubautroi.vercel.app"
API = {k:f"{BASE_URL}/api/{v}" for k,v in {
    "user":"user","checkin":"check-in","start":"start",
    "jump":"jump","sync":"sync","check":"check","apply":"apply"
}.items()}

DEFAULT_CFG = {
    # Timing constraints
    "crash_pre_offset": 100,    # ms: Nhảy TRƯỚC nổ 100ms (an toàn)
    "auto_post_delay": 0,       # ms: Nhảy SAU nổ 0ms (chờ hết round)
    
    # System
    "min_energy": 5,
    "debug": True,
    
    # Network
    "latency_compensation": True, # Trừ 1/2 RTT vào wait time
    
    # Money
    "stop_loss": 0,             # Dừng nếu thua quá số này
    "take_profit": 0            # Dừng nếu lãi quá số này
}

def decode_jwt(token):
    try:
        parts = token.split(".")
        b64 = parts[1] + "=" * (4 - len(parts[1]) % 4)
        return json.loads(base64.urlsafe_b64decode(b64))
    except: return None

class BoTheoDoi:
    """Theo dõi lợi nhuận V5"""
    def __init__(self):
        self.start_time = time.time()
        self.wins = 0; self.losses = 0
        self.profit = 0; self.energy_spent = 0
        self.streak = 0; self.max_streak = 0
        self.history = deque(maxlen=20)
        self.max_win = 0

    def record(self, earned, energy_lost, is_win):
        self.energy_spent += energy_lost
        if is_win:
            self.wins += 1
            self.profit += earned
            self.streak += 1
            self.max_streak = max(self.max_streak, self.streak)
            self.max_win = max(self.max_win, earned)
            self.history.append(1)
        else:
            self.losses += 1
            self.streak = 0
            self.history.append(0)

    @property
    def win_rate(self):
        total = self.wins + self.losses
        return (self.wins / total * 100) if total > 0 else 0

    @property
    def hourly_profit(self):
        hours = (time.time() - self.start_time) / 3600
        return self.profit / hours if hours > 0.001 else 0

    @property
    def roi(self):
        return (self.profit / self.energy_spent * 100) if self.energy_spent > 0 else 0

    def summary(self):
        elapsed = time.time() - self.start_time
        g, r = divmod(int(elapsed), 3600); p, _ = divmod(r, 60)
        return (
            f"📊 {self.wins}W/{self.losses}L ({self.win_rate:.0f}%) | "
            f"💰 {fmoney(self.profit)} | "
            f"⚡ROI: {self.roi:.0f}% | "
            f"💵/h: {fmoney(int(self.hourly_profit))} | "
            f"🔥 Chuỗi: {self.streak} | "
            f"⏱️ {g}g{p:02d}p"
        )

class AutoTyHubV5:
    def __init__(self, index, init_data, config):
        self.idx = index
        self.init_data = init_data
        self.config = config
        self.session = None
        self.running = True
        self.tracker = BoTheoDoi()

        # Account state
        self.username = "?"
        self.balance = 0
        self.start_balance = 0
        self.energy = 0
        self.max_energy = 6000
        
        # V6 QUANTUM Synchronization & Jitter Matrix
        self.clock_offset = 0       # ms: server_time - local_time
        self.rtt_history = deque(maxlen=20)
        self.avg_rtt = 100          
        self.network_jitter = 10.0  # Độ lệch chuẩn mạng (chống loss tuyệt đối)
        self.next_refill_at = 0     
        self.next_energy_ad_time = 0 # Cooldown nhiệm vụ tiếp tế lộ hổng

        self.pfx = f"{M.C}[#{self.idx}]{M.X}"

    async def quantum_sleep(self, duration_s):
        """Khóa thời gian lượng tử (độ trễ micro giây)"""
        if duration_s <= 0: return
        # Trao lại luồng nếu thời gian chờ lớn
        if duration_s > 0.05:
            await asyncio.sleep(duration_s - 0.05)
        # Busy-wait cho 50ms cuối cùng để khóa độ lệch
        target = time.perf_counter() + (duration_s if duration_s <= 0.05 else 0.05)
        while time.perf_counter() < target:
            pass

    def log(self, icon, msg, c=M.W):
        print(f"{M.GR}[{ts()}]{M.X} {self.pfx} {c}[{icon}]{M.X} {msg}")
    def ok(self, m):   self.log("✅", m, M.G)
    def err(self, m):  self.log("❌", m, M.R)
    def warn(self, m): self.log("⚠️", m, M.Y)
    def info(self, m): self.log("ℹ️", m, M.B)
    def stat(self, m): self.log("📊", m, M.P)

    def dbg(self, tag, m, color=None):
        if not self.config.get("debug", False): return
        colors = {"API":M.DBG_API,"JWT":M.DBG_JWT,"TIME":M.DBG_TIME,"RES":M.DBG_RES,"ERR":M.DBG_ERR,"SYS":M.DBG_SYS}
        c = color or colors.get(tag, M.GR)
        print(f"{M.GR}[{ts()}]{M.X} {self.pfx} {c}[🐛 {tag}]{M.X} {c}{m}{M.X}")

    def dbg_sep(self, m):
        if self.config.get("debug", False):
            print(f"{M.GR}[{ts()}]{M.X} {self.pfx} {M.DBG_SEP}{m}{M.X}")

    def _headers(self):
        return {
            'accept': '*/*', 'content-type': 'application/json',
            'origin': BASE_URL, 'referer': f'{BASE_URL}/',
            'x-init-data': self.init_data,
            'user-agent': 'Mozilla/5.0 (Linux; Android 14; SM-S928B) AppleWebKit/537.36'
        }

    async def req(self, url, payload=None, tag="", silent=False):
        if not self.session: return None, None
        t0 = time.time()
        try:
            async with self.session.post(url, json=payload or {}, headers=self._headers(),
                                         timeout=aiohttp.ClientTimeout(total=15)) as r:
                txt = await r.text()
                rtt = (time.time() - t0) * 1000
                
                # Update Quantum RTT stats
                self.rtt_history.append(rtt)
                self.avg_rtt = statistics.mean(self.rtt_history)
                self.network_jitter = statistics.stdev(self.rtt_history) if len(self.rtt_history) > 1 else 10.0

                try: d = json.loads(txt)
                except: d = txt
                
                if not silent: self.dbg("API", f"[{r.status}] {tag} | RTT={rtt:.0f}ms")
                
                if r.status == 401: return 401, d
                return r.status, d
        except Exception as e:
            if not silent: self.err(f"{tag}: {e}")
            return None, None

    async def login(self):
        s, d = await self.req(API["user"], tag="LOGIN", silent=True)
        if s == 200 and isinstance(d, dict):
            self.username = d.get("username", "?")
            self.balance = d.get("balance", 0)
            self.start_balance = self.balance
            self.energy = d.get("energy", 0)
            self.max_energy = d.get("baseMaxEnergy", 6000)
            self.is_claimed_today = d.get("isClaimedToday", False)
            self.dbg("SYS", f"User: {self.username} | Bal: {fmoney(self.balance)} | E: {self.energy}")
            return True
        return False

    async def sync_clock(self):
        """Đồng bộ thời gian server & cập nhật NL status"""
        t_pre = time.time() * 1000
        s, d = await self.req(API["sync"], tag="SYNC", silent=True)
        t_post = time.time() * 1000
        
        if s == 200 and isinstance(d, dict):
            self.balance = d.get("balance", self.balance)
            self.energy = d.get("energy", self.energy)
            
            # Sync logic
            server_time = d.get("server_time", 0)
            if server_time:
                local_mid = (t_pre + t_post) / 2
                offset = server_time - local_mid
                # Weighted update (ưu tiên giá trị mới 70%)
                if self.clock_offset == 0: self.clock_offset = offset
                else: self.clock_offset = (self.clock_offset * 0.3) + (offset * 0.7)
                
            self.next_refill_at = d.get("nextRefillAt", 0)
            self.dbg("SYS", f"Sync: E={self.energy} | Offset={self.clock_offset:+.0f}ms | RTT={self.avg_rtt:.0f}ms")
            return True
        return False

    async def check_in(self):
        """Tự động điểm danh hàng ngày"""
        if getattr(self, 'is_claimed_today', False):
            self.ok("🎁 Điểm danh: Đã nhận từ trước.")
            return True
            
        s, d = await self.req(API["checkin"], tag="CHECK-IN", silent=False)
        if s == 200:
            reward = d.get("reward", 0) if isinstance(d, dict) else 0
            if reward:
                self.ok(f"🎁 Điểm danh thành công! Nhận {fmoney(reward)}")
            else:
                self.ok("🎁 Điểm danh thành công!")
            self.is_claimed_today = True
            return True
        elif s == 400:
            err = d.get("error", "") if isinstance(d, dict) else str(d)
            if "already" in err.lower() or "đã nhận" in err.lower() or "hôm nay" in err.lower():
                self.ok("🎁 Điểm danh: Đã nhận từ trước.")
                self.is_claimed_today = True
                return True
            self.warn(f"Điểm danh lỗi: {err}")
        return False

    async def claim_energy_ad(self):
        """Auto húp Kim Cương Nhiệm Vụ Tiếp Tế mỗi 15p (không cần xem QC)"""
        if time.time() < self.next_energy_ad_time: return True
        
        s, d = await self.req(API["apply"], {"type": "energy"}, tag="AD_ENERGY", silent=True)
        if s == 200:
            reward = d.get("reward", 0) if isinstance(d, dict) else 0
            self.ok(f"💎 [BYPASS QC] Lụm {fnum(reward)} Kim Cương Tiếp Tế! (15p/lần)")
            self.next_energy_ad_time = time.time() + 15.5 * 60
            self.diamond = self.diamond + reward if hasattr(self, 'diamond') else reward
            return True
        elif s == 400:
            err = d.get("error", "") if isinstance(d, dict) else str(d)
            if "chờ" in err.lower() or "phút" in err.lower():
                import re
                minutes = re.findall(r'\d+', err)
                wait_mins = int(minutes[0]) if minutes else 15
                self.dbg("SYS", f"💎 Tiếp Tế: Cooldown {wait_mins}p")
                self.next_energy_ad_time = time.time() + wait_mins * 60 + 10
            else:
                self.warn(f"💎 Tiếp Tế lỗi: {err}")
                self.next_energy_ad_time = time.time() + 5 * 60
        return False

    async def play_round(self):
        self.dbg_sep(f"{'─'*15} ROUND #{self.tracker.wins + self.tracker.losses + 1} {'─'*15}")
        
        # 1. Start Game
        s, d = await self.req(API["start"], tag="START", silent=True)
        if s != 200 or not d.get("ok"):
            err = d.get("error", "?") if isinstance(d, dict) else "?"
            if s == 401: return "auth_fail"
            self.warn(f"Start fail: {err}")
            return "retry"

        token = d.get("payload")
        jwt = decode_jwt(token)
        if not jwt or "crashTime" not in jwt:
            self.err("JWT Fail")
            return "retry"

        # 2. Analyze Timing
        crash_ms = jwt["crashTime"]
        bet = jwt.get("energyLost", 0)
        mode = jwt.get("mode", "AUTO")
        now_ms = time.time() * 1000
        
        # Local view of "time until crash"
        server_now = now_ms + self.clock_offset
        wait_ms = crash_ms - server_now
        
        # 3. KÍCH HOẠT LƯỚI BẢO VỆ ZERO-LOSS (AI Jitter Matrix)
        # Sàn an toàn tuyệt đối tính dựa trên sóng giật của mạng (Jitter)
        safe_floor = self.network_jitter * 1.5 + (self.avg_rtt * 0.2) + 15
        if not hasattr(self, 'current_pre_offset'):
            self.current_pre_offset = max(100, safe_floor)
            
        if mode == "CRASH":
            # Tự động hút cạn lãi (Squeeze) nhưng KẸT CỨNG tại safe_floor
            target_offset = -max(safe_floor, self.current_pre_offset)
            strat = f"PRE {int(-target_offset)}ms (P99 🛡️:{int(safe_floor)}ms)"
        else:
            target_offset = self.config["auto_post_delay"] # 0ms
            strat = "POST 0ms"

        # 4. Latency Compensation Định Tuyến
        latency_comp = self.avg_rtt / 2 if self.config["latency_compensation"] else 0
        
        final_wait_ms = wait_ms + target_offset - latency_comp
        final_wait_s = max(0, final_wait_ms / 1000)

        self.info(f"🔮 {mode} | Burst {wait_ms/1000:.2f}s | Lệnh: {strat} | Bù Trễ: -{int(latency_comp)}ms")
        self.dbg("TIME", f"⏳ Kích hoạt Quantum Lock chốt {final_wait_s:.4f}s...")
        
        await self.quantum_sleep(final_wait_s)
        
        # 5. Jump (Kích Nổ)
        t_jump = time.time() * 1000
        s, d = await self.req(API["jump"], {"payload": token}, tag="JUMP", silent=True)
        
        delta_real = t_jump + self.clock_offset - crash_ms
        self.dbg("TIME", f"Jump Delta (vs Server Crash): {delta_real:+.0f}ms")

        # 6. Handle Result
        if s == 200 and d.get("ok"):
            earned = d.get("earned", 0)
            refund = d.get("refundedEnergy", 0)
            type_ = d.get("type", "?")
            
            if earned > 0:
                self.ok(f"💰 WON +{fmoney(earned)} ({mode}) | {type_}")
                if refund: self.energy += refund
                self.balance += earned
                self.tracker.record(earned, bet, True)
                
                # NẾU THẮNG: Vắt kiệt mốc lợi nhuận xuống sát Lưới Bảo Vệ
                if mode == "CRASH":
                    old_offset = self.current_pre_offset
                    self.current_pre_offset = max(safe_floor, self.current_pre_offset - 4.5)
                    if old_offset != self.current_pre_offset:
                        self.dbg("SYS", f"🌀 Lượng Tử: Siết {old_offset:.0f}ms -> {self.current_pre_offset:.0f}ms")
                await asyncio.sleep(0.1) 
                return "win"
            else:
                self.err(f"💀 LOSS -{bet}⚡ ({mode}) | {type_}")
                self.tracker.record(0, bet, False)
                
                # NẾU THUA: Mạng biến động! Chống sập bằng Mảng Phản Lực Jitter
                if mode == "CRASH":
                    old_offset = self.current_pre_offset
                    self.current_pre_offset = min(500, self.current_pre_offset + self.network_jitter * 3 + 100)
                    self.dbg("SYS", f"🛡️ Cấp Cứu: Nới rào chắn {old_offset:.0f}ms -> {self.current_pre_offset:.0f}ms")
                return "loss"
        elif s == 401:
            return "auth_fail"
        else:
            err = d.get("error", "?") if isinstance(d, dict) else "?"
            if "expired" in str(err): return "retry"
            self.err(f"Jump Fail: {err}")
            return "retry"

    async def run(self):
        self.session = aiohttp.ClientSession(connector=aiohttp.TCPConnector(limit=5, ssl=False))
        try:
            if not await self.login():
                self.err("Login Fail! Check init-data.")
                return

            self.ok(f"🚀 V5 TURBO STARTED | {self.username}")
            
            # Initial Sync
            await self.sync_clock()
            
            # Daily Check-in
            await self.check_in()

            while self.running:
                # 0. Húp QC Tiếp tế (Không xem video)
                await self.claim_energy_ad()
                
                # 1. Energy Check
                if self.energy < self.config["min_energy"]:
                    if self.next_refill_at > 0:
                        now_ms = time.time() * 1000
                        # Thêm 1s buffer để chắc chắn server đã update
                        wait_s = (self.next_refill_at - (now_ms + self.clock_offset)) / 1000 + 1.0
                        wait_s = max(1, wait_s)
                        
                        if wait_s < 300: # Wait nếu < 5 phút
                            self.warn(f"⚡ Low Energy ({self.energy}). Refill in {wait_s:.1f}s...")
                            await asyncio.sleep(wait_s)
                            await self.sync_clock()
                            continue
                            
                    # Fallback poll
                    self.warn(f"⚡ Low Energy ({self.energy}). Polling...")
                    await asyncio.sleep(10)
                    await self.sync_clock()
                    continue

                # 2. Play
                res = await self.play_round()
                
                if res == "auth_fail":
                    self.err("Auth Error. Re-login in 30s...")
                    await asyncio.sleep(30)
                    if not await self.login(): break
                elif res == "retry":
                    await asyncio.sleep(1)
                
                # 3. Stats Log
                if self.tracker.wins + self.tracker.losses > 0 and (self.tracker.wins + self.tracker.losses) % 5 == 0:
                     self.stat(self.tracker.summary())

        except asyncio.CancelledError:
            pass
        except Exception as e:
            self.err(f"Crash: {e}")
        finally:
            await self.session.close()
            print(f"\n{self.pfx} STOPPED. Final Profit: {fmoney(self.tracker.profit)}")

async def main():
    config = dict(DEFAULT_CFG)
    # Load config file if valid
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r") as f:
                c = json.load(f)
                config.update(c)
        except: pass

    os.system('cls' if os.name == 'nt' else 'clear')
    print(f"""{M.C}{M.D}
╔═══════════════════════════════════════════════════════════╗
║        🌌 AUTO TYHUB V6 QUANTUM - MAXIMUM LIMIT MODE      ║
║   [■] MICROSECOND SYNC | [■] AI JITTER PREDICTION MATRX   ║
║   [■] ZERO LOSS PROTOCOL ACTIVE | PROFIT SQUEEZE AT MAX   ║
╚═══════════════════════════════════════════════════════════╝{M.X}""")

    tokens = []
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f: tokens = [l.strip() for l in f if l.strip()]
    if not tokens and os.path.exists(INIT_DATA_FILE):
        with open(INIT_DATA_FILE, "r") as f: 
            t = f.read().strip()
            if t: tokens = [t]
            
    if not tokens:
        print(f"{M.R}Missing {DATA_FILE} or {INIT_DATA_FILE}{M.X}")
        return

    print(f"Loaded {len(tokens)} accounts.")
    bots = [AutoTyHubV5(i+1, t, config) for i,t in enumerate(tokens)]
    
    try:
        await asyncio.gather(*(b.run() for b in bots))
    except KeyboardInterrupt:
        for b in bots: b.running = False


if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    try: asyncio.run(main())
    except KeyboardInterrupt: pass

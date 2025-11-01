import hashlib
import time
import multiprocessing as mp
import math

LETTERS = "ABEKMHOPCTYX"
REGIONS = [f"{i:02d}" for i in range(1, 100)] + \
          [str(i) for i in range(100, 200)] + \
          [str(i) for i in range(700, 800)] + \
          [str(i) for i in range(900, 1000)]

def worker(first_letters_chunk, target_md5_bytes, target_sha256_bytes, regions):
    letters_b = [c.encode("utf-8") for c in LETTERS]
    nums_b = [f"{i:03d}".encode("utf-8") for i in range(1000)]
    pairs_b = [ (l2.encode("utf-8") + l3.encode("utf-8")) for l2 in LETTERS for l3 in LETTERS ]
    regions_b = [r.encode("utf-8") for r in regions]
    first_b_list = [c.encode("utf-8") for c in first_letters_chunk]

    # Перебор
    for b1 in first_b_list:
        for num_b in nums_b:
            base_prefix = b1 + num_b
            for pair in pairs_b:
                base = base_prefix + pair
                md5_base = hashlib.md5(base)
                for reg_b in regions_b:
                    md5_obj = md5_base.copy()
                    md5_obj.update(reg_b)
                    if md5_obj.digest() != target_md5_bytes:
                        continue
                    plate_bytes = base + reg_b
                    if hashlib.sha256(plate_bytes).digest() == target_sha256_bytes:
                        try:
                            return plate_bytes.decode("utf-8")
                        except Exception:
                            return repr(plate_bytes)
    return None


def chunk_letters(letters, n_chunks):
    letters_list = list(letters)
    k = math.ceil(len(letters_list) / n_chunks)
    return [letters_list[i:i+k] for i in range(0, len(letters_list), k)]


def solve_multiproc(target_md5_hex, target_sha256_hex, regions=REGIONS, processes=None):
    target_md5 = bytes.fromhex(target_md5_hex.lower())
    target_sha256 = bytes.fromhex(target_sha256_hex.lower())

    if processes is None:
        processes = max(1, mp.cpu_count() - 1)
    processes = min(processes, len(LETTERS))

    letter_chunks = chunk_letters(LETTERS, processes)
    combos_estimate = len(LETTERS) * 1000 * (len(LETTERS)**2) * len(regions)
    print("py_hash_lib/run.py")
    print(f"~{combos_estimate/1000:.1f} тыс возможных результатов (оценка)")
    print(f"Используем процессов: {processes}")

    start = time.perf_counter()

    pool = mp.Pool(processes=processes)
    async_results = []
    try:
        for chunk in letter_chunks:
            async_results.append(pool.apply_async(
                worker,
                (chunk, target_md5, target_sha256, regions)
            ))
        found = None
        while async_results:
            for i, ar in enumerate(async_results):
                if ar.ready():
                    res = ar.get()
                    if res:
                        found = res
                        break
                    else:
                        async_results.pop(i)
                        break
            if found:
                break
            time.sleep(0.05)

        elapsed = time.perf_counter() - start
        if found:
            pool.terminate()
            pool.join()
            print(f"|| {found} ||")
            print(f"Время выполнения функции {elapsed:.3f} сек.")
            return found
        else:
            pool.close()
            pool.join()
            print("Не найдено")
            print(f"Время выполнения функции {elapsed:.3f} сек.")
            return None

    except KeyboardInterrupt:
        pool.terminate()
        pool.join()
        print("Прервано пользователем")
        raise
    except Exception as e:
        pool.terminate()
        pool.join()
        raise


if __name__ == "__main__":
    target_md5 = "743f0ed26d2bff34fb9a335588238ceb"
    target_sha256 = "ef581243eb6f7fa74ce03466b9051464275c6b34017a6f031f2548a6d5d0b711"

    result = solve_multiproc(target_md5, target_sha256, regions=["77","78","50","97","99","177","199","196"])
    if result:
        print("Найден номер:", result)
    else:
        print("Совпадений не найдено на выбранных регионах.")

def analyze(nums):
    for num in nums:
        if num > 0:
            for i in range(num):
                if i % 2 == 0:
                    print(i)
# 第12章：DeFi 应用开发

本章学习去中心化金融（DeFi）应用的开发，包括简单的 DEX、质押系统等。

## 12.1 DeFi 基础概念

### 什么是 DeFi？
去中心化金融是基于区块链的金融服务，无需中介即可进行：
- 💱 交易（DEX）
- 💰 借贷
- 🏦 存款生息
- 🎲 衍生品交易
- 💎 资产管理

### DeFi vs 传统金融
```
┌──────────────────────────────────────────────────┐
│ 特性      │ 传统金融        │ DeFi              │
├──────────────────────────────────────────────────┤
│ 中介      │ 银行、券商      │ 智能合约          │
│ 开放性    │ 需要审批        │ 无需许可          │
│ 透明度    │ 不透明          │ 完全透明          │
│ 可访问性  │ 有限制          │ 全球无限制        │
│ 手续费    │ 较高            │ 较低              │
│ 速度      │ T+1/T+2         │ 实时              │
└──────────────────────────────────────────────────┘
```

## 12.2 简单的 DEX（去中心化交易所）

### 自动做市商（AMM）原理
使用恒定乘积公式：`x * y = k`
- x: Token A 的数量
- y: Token B 的数量
- k: 常数

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

interface IERC20 {
    function transfer(address to, uint256 amount) external returns (bool);
    function transferFrom(address from, address to, uint256 amount) external returns (bool);
    function balanceOf(address account) external view returns (uint256);
}

contract SimpleDEX {
    IERC20 public tokenA;
    IERC20 public tokenB;

    uint256 public reserveA;
    uint256 public reserveB;

    uint256 public totalLiquidity;
    mapping(address => uint256) public liquidity;

    event LiquidityAdded(address indexed provider, uint256 amountA, uint256 amountB, uint256 liquidityMinted);
    event LiquidityRemoved(address indexed provider, uint256 amountA, uint256 amountB, uint256 liquidityBurned);
    event Swap(address indexed trader, address tokenIn, uint256 amountIn, uint256 amountOut);

    constructor(address _tokenA, address _tokenB) {
        tokenA = IERC20(_tokenA);
        tokenB = IERC20(_tokenB);
    }

    // 添加流动性
    function addLiquidity(uint256 amountA, uint256 amountB)
        external
        returns (uint256 liquidityMinted)
    {
        require(amountA > 0 && amountB > 0, "Amounts must be greater than 0");

        // 转入代币
        tokenA.transferFrom(msg.sender, address(this), amountA);
        tokenB.transferFrom(msg.sender, address(this), amountB);

        // 计算流动性份额
        if (totalLiquidity == 0) {
            // 第一次添加流动性
            liquidityMinted = sqrt(amountA * amountB);
        } else {
            // 后续添加流动性：按比例计算
            uint256 liquidityA = (amountA * totalLiquidity) / reserveA;
            uint256 liquidityB = (amountB * totalLiquidity) / reserveB;
            liquidityMinted = min(liquidityA, liquidityB);
        }

        require(liquidityMinted > 0, "Liquidity minted must be greater than 0");

        // 更新储备
        reserveA += amountA;
        reserveB += amountB;
        totalLiquidity += liquidityMinted;
        liquidity[msg.sender] += liquidityMinted;

        emit LiquidityAdded(msg.sender, amountA, amountB, liquidityMinted);

        return liquidityMinted;
    }

    // 移除流动性
    function removeLiquidity(uint256 liquidityAmount)
        external
        returns (uint256 amountA, uint256 amountB)
    {
        require(liquidityAmount > 0, "Liquidity must be greater than 0");
        require(liquidity[msg.sender] >= liquidityAmount, "Insufficient liquidity");

        // 计算可以取回的代币数量
        amountA = (liquidityAmount * reserveA) / totalLiquidity;
        amountB = (liquidityAmount * reserveB) / totalLiquidity;

        require(amountA > 0 && amountB > 0, "Insufficient liquidity burned");

        // 更新储备
        reserveA -= amountA;
        reserveB -= amountB;
        totalLiquidity -= liquidityAmount;
        liquidity[msg.sender] -= liquidityAmount;

        // 转出代币
        tokenA.transfer(msg.sender, amountA);
        tokenB.transfer(msg.sender, amountB);

        emit LiquidityRemoved(msg.sender, amountA, amountB, liquidityAmount);

        return (amountA, amountB);
    }

    // 交换 A -> B
    function swapAforB(uint256 amountAIn) external returns (uint256 amountBOut) {
        require(amountAIn > 0, "Amount must be greater than 0");

        // 计算输出数量（恒定乘积公式）
        // (x + Δx) * (y - Δy) = k
        // Δy = (y * Δx) / (x + Δx)
        uint256 amountBOutNoFee = (reserveB * amountAIn) / (reserveA + amountAIn);

        // 扣除 0.3% 手续费
        amountBOut = (amountBOutNoFee * 997) / 1000;

        require(amountBOut > 0, "Insufficient output amount");
        require(reserveB > amountBOut, "Insufficient liquidity");

        // 转入 A，转出 B
        tokenA.transferFrom(msg.sender, address(this), amountAIn);
        tokenB.transfer(msg.sender, amountBOut);

        // 更新储备
        reserveA += amountAIn;
        reserveB -= amountBOut;

        emit Swap(msg.sender, address(tokenA), amountAIn, amountBOut);

        return amountBOut;
    }

    // 交换 B -> A
    function swapBforA(uint256 amountBIn) external returns (uint256 amountAOut) {
        require(amountBIn > 0, "Amount must be greater than 0");

        uint256 amountAOutNoFee = (reserveA * amountBIn) / (reserveB + amountBIn);
        amountAOut = (amountAOutNoFee * 997) / 1000;

        require(amountAOut > 0, "Insufficient output amount");
        require(reserveA > amountAOut, "Insufficient liquidity");

        tokenB.transferFrom(msg.sender, address(this), amountBIn);
        tokenA.transfer(msg.sender, amountAOut);

        reserveB += amountBIn;
        reserveA -= amountAOut;

        emit Swap(msg.sender, address(tokenB), amountBIn, amountAOut);

        return amountAOut;
    }

    // 获取交换价格
    function getAmountOut(uint256 amountIn, uint256 reserveIn, uint256 reserveOut)
        public
        pure
        returns (uint256 amountOut)
    {
        require(amountIn > 0, "Insufficient input amount");
        require(reserveIn > 0 && reserveOut > 0, "Insufficient liquidity");

        uint256 amountInWithFee = amountIn * 997;
        uint256 numerator = amountInWithFee * reserveOut;
        uint256 denominator = (reserveIn * 1000) + amountInWithFee;

        amountOut = numerator / denominator;
    }

    // 辅助函数
    function min(uint256 a, uint256 b) internal pure returns (uint256) {
        return a < b ? a : b;
    }

    function sqrt(uint256 y) internal pure returns (uint256 z) {
        if (y > 3) {
            z = y;
            uint256 x = y / 2 + 1;
            while (x < z) {
                z = x;
                x = (y / x + x) / 2;
            }
        } else if (y != 0) {
            z = 1;
        }
    }
}
```

## 12.3 质押奖励系统

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract StakingRewards {
    IERC20 public stakingToken;
    IERC20 public rewardsToken;

    uint256 public rewardRate = 100;  // 每秒的奖励数量
    uint256 public lastUpdateTime;
    uint256 public rewardPerTokenStored;

    mapping(address => uint256) public userRewardPerTokenPaid;
    mapping(address => uint256) public rewards;

    uint256 private _totalSupply;
    mapping(address => uint256) private _balances;

    event Staked(address indexed user, uint256 amount);
    event Withdrawn(address indexed user, uint256 amount);
    event RewardPaid(address indexed user, uint256 reward);

    constructor(address _stakingToken, address _rewardsToken) {
        stakingToken = IERC20(_stakingToken);
        rewardsToken = IERC20(_rewardsToken);
        lastUpdateTime = block.timestamp;
    }

    // 计算每个 token 的奖励
    function rewardPerToken() public view returns (uint256) {
        if (_totalSupply == 0) {
            return rewardPerTokenStored;
        }

        return rewardPerTokenStored +
            (((block.timestamp - lastUpdateTime) * rewardRate * 1e18) / _totalSupply);
    }

    // 计算用户的奖励
    function earned(address account) public view returns (uint256) {
        return ((_balances[account] *
            (rewardPerToken() - userRewardPerTokenPaid[account])) / 1e18) +
            rewards[account];
    }

    // 质押
    function stake(uint256 amount) external updateReward(msg.sender) {
        require(amount > 0, "Cannot stake 0");

        _totalSupply += amount;
        _balances[msg.sender] += amount;

        stakingToken.transferFrom(msg.sender, address(this), amount);

        emit Staked(msg.sender, amount);
    }

    // 提取质押
    function withdraw(uint256 amount) public updateReward(msg.sender) {
        require(amount > 0, "Cannot withdraw 0");
        require(_balances[msg.sender] >= amount, "Insufficient balance");

        _totalSupply -= amount;
        _balances[msg.sender] -= amount;

        stakingToken.transfer(msg.sender, amount);

        emit Withdrawn(msg.sender, amount);
    }

    // 领取奖励
    function getReward() public updateReward(msg.sender) {
        uint256 reward = rewards[msg.sender];
        if (reward > 0) {
            rewards[msg.sender] = 0;
            rewardsToken.transfer(msg.sender, reward);
            emit RewardPaid(msg.sender, reward);
        }
    }

    // 退出：提取所有质押和奖励
    function exit() external {
        withdraw(_balances[msg.sender]);
        getReward();
    }

    // 查询函数
    function totalSupply() external view returns (uint256) {
        return _totalSupply;
    }

    function balanceOf(address account) external view returns (uint256) {
        return _balances[account];
    }

    // 更新奖励的修饰器
    modifier updateReward(address account) {
        rewardPerTokenStored = rewardPerToken();
        lastUpdateTime = block.timestamp;

        if (account != address(0)) {
            rewards[account] = earned(account);
            userRewardPerTokenPaid[account] = rewardPerTokenStored;
        }

        _;
    }

    // Owner 设置奖励率
    function setRewardRate(uint256 _rewardRate) external {
        rewardRate = _rewardRate;
    }
}
```

## 12.4 借贷协议

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract SimpleLending {
    IERC20 public token;

    // 利率：年化利率（基点，1% = 100）
    uint256 public constant INTEREST_RATE = 500;  // 5%
    uint256 public constant COLLATERAL_RATIO = 150;  // 150% 抵押率

    struct Loan {
        uint256 collateral;      // 抵押物数量
        uint256 borrowed;        // 借款数量
        uint256 timestamp;       // 借款时间
    }

    mapping(address => Loan) public loans;
    mapping(address => uint256) public deposits;

    uint256 public totalDeposits;
    uint256 public totalBorrowed;

    event Deposited(address indexed user, uint256 amount);
    event Withdrawn(address indexed user, uint256 amount);
    event Borrowed(address indexed user, uint256 amount, uint256 collateral);
    event Repaid(address indexed user, uint256 amount, uint256 interest);
    event Liquidated(address indexed user, address indexed liquidator, uint256 amount);

    constructor(address _token) {
        token = IERC20(_token);
    }

    // 存款
    function deposit(uint256 amount) external {
        require(amount > 0, "Amount must be greater than 0");

        token.transferFrom(msg.sender, address(this), amount);

        deposits[msg.sender] += amount;
        totalDeposits += amount;

        emit Deposited(msg.sender, amount);
    }

    // 提款
    function withdraw(uint256 amount) external {
        require(amount > 0, "Amount must be greater than 0");
        require(deposits[msg.sender] >= amount, "Insufficient balance");

        deposits[msg.sender] -= amount;
        totalDeposits -= amount;

        token.transfer(msg.sender, amount);

        emit Withdrawn(msg.sender, amount);
    }

    // 借款
    function borrow(uint256 amount) external payable {
        require(amount > 0, "Amount must be greater than 0");
        require(msg.value > 0, "Must provide collateral");

        // 检查抵押率
        uint256 requiredCollateral = (amount * COLLATERAL_RATIO) / 100;
        require(msg.value >= requiredCollateral, "Insufficient collateral");

        // 检查流动性
        require(totalDeposits >= totalBorrowed + amount, "Insufficient liquidity");

        Loan storage loan = loans[msg.sender];
        loan.collateral += msg.value;
        loan.borrowed += amount;
        loan.timestamp = block.timestamp;

        totalBorrowed += amount;

        token.transfer(msg.sender, amount);

        emit Borrowed(msg.sender, amount, msg.value);
    }

    // 还款
    function repay(uint256 amount) external {
        Loan storage loan = loans[msg.sender];
        require(loan.borrowed > 0, "No active loan");

        // 计算利息
        uint256 interest = calculateInterest(msg.sender);
        uint256 totalOwed = loan.borrowed + interest;

        require(amount <= totalOwed, "Amount exceeds debt");

        token.transferFrom(msg.sender, address(this), amount);

        if (amount >= totalOwed) {
            // 全额还款
            uint256 collateralToReturn = loan.collateral;

            delete loans[msg.sender];
            totalBorrowed -= loan.borrowed;

            payable(msg.sender).transfer(collateralToReturn);

            emit Repaid(msg.sender, loan.borrowed, interest);
        } else {
            // 部分还款
            uint256 principalPaid = amount - interest;

            loan.borrowed -= principalPaid;
            loan.timestamp = block.timestamp;

            totalBorrowed -= principalPaid;

            emit Repaid(msg.sender, principalPaid, interest);
        }
    }

    // 清算
    function liquidate(address borrower) external {
        Loan storage loan = loans[borrower];
        require(loan.borrowed > 0, "No active loan");

        // 检查是否需要清算（抵押率低于 120%）
        uint256 currentCollateralRatio = (loan.collateral * 100) / loan.borrowed;
        require(currentCollateralRatio < 120, "Loan is healthy");

        uint256 interest = calculateInterest(borrower);
        uint256 totalOwed = loan.borrowed + interest;

        // 清算人支付债务
        token.transferFrom(msg.sender, address(this), totalOwed);

        // 清算人获得抵押物
        uint256 collateral = loan.collateral;
        delete loans[borrower];

        totalBorrowed -= loan.borrowed;

        payable(msg.sender).transfer(collateral);

        emit Liquidated(borrower, msg.sender, totalOwed);
    }

    // 计算利息
    function calculateInterest(address borrower) public view returns (uint256) {
        Loan memory loan = loans[borrower];

        if (loan.borrowed == 0) return 0;

        uint256 timeElapsed = block.timestamp - loan.timestamp;
        uint256 annualInterest = (loan.borrowed * INTEREST_RATE) / 10000;
        uint256 interest = (annualInterest * timeElapsed) / 365 days;

        return interest;
    }

    // 查询健康因子
    function getHealthFactor(address borrower) external view returns (uint256) {
        Loan memory loan = loans[borrower];

        if (loan.borrowed == 0) return type(uint256).max;

        return (loan.collateral * 100) / loan.borrowed;
    }

    // 查询可用流动性
    function getAvailableLiquidity() external view returns (uint256) {
        return totalDeposits - totalBorrowed;
    }
}
```

## 12.5 价格预言机集成

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

// Chainlink 价格预言机接口
interface AggregatorV3Interface {
    function latestRoundData()
        external
        view
        returns (
            uint80 roundId,
            int256 answer,
            uint256 startedAt,
            uint256 updatedAt,
            uint80 answeredInRound
        );
}

contract PriceConsumer {
    AggregatorV3Interface internal priceFeed;

    constructor(address _priceFeed) {
        priceFeed = AggregatorV3Interface(_priceFeed);
    }

    // 获取最新价格
    function getLatestPrice() public view returns (int256) {
        (, int256 price, , , ) = priceFeed.latestRoundData();
        return price;
    }

    // 使用价格进行计算
    function calculateValue(uint256 amount) public view returns (uint256) {
        int256 price = getLatestPrice();
        require(price > 0, "Invalid price");

        return (amount * uint256(price)) / 1e8;  // Chainlink 价格精度为 8 位
    }
}
```

## 📝 实践任务

### 任务 1：改进 DEX
在简单 DEX 基础上添加：
- 手续费分配给流动性提供者
- 滑点保护
- 紧急暂停功能
- 管理员功能

### 任务 2：时间锁定质押
创建质押合约：
- 不同锁定期有不同奖励率
- 提前解锁需要罚金
- 奖励自动复投功能
- 质押凭证 NFT

### 任务 3：闪电贷
实现简单的闪电贷：
- 单次交易内借贷和还款
- 手续费机制
- 防止重入攻击
- 测试套利场景

## 📝 本章小结

- ✅ 理解 DeFi 核心概念
- ✅ 实现简单的 DEX（AMM）
- ✅ 创建质押奖励系统
- ✅ 开发借贷协议
- ✅ 集成价格预言机

## 🎯 安全提示

1. **价格操纵**：使用可信的价格预言机
2. **闪电贷攻击**：防范价格瞬时操纵
3. **重入攻击**：遵循 CEI 模式
4. **整数溢出**：使用 SafeMath 或 0.8.0+
5. **流动性风险**：确保有足够的流动性
6. **审计**：DeFi 合约必须经过专业审计

## 🎓 教程总结

恭喜你完成了 Solidity 完整学习教程！

### 你已经掌握：
✅ 区块链和智能合约基础
✅ Solidity 语法和核心特性
✅ 合约开发、测试、部署流程
✅ ERC20 代币开发
✅ NFT (ERC721) 开发
✅ DeFi 应用开发

### 下一步建议：
1. **深入学习**：阅读 Solidity 官方文档
2. **实战项目**：参与开源项目或创建自己的 DApp
3. **安全审计**：学习常见漏洞和审计技术
4. **关注社区**：参与以太坊社区讨论
5. **持续学习**：区块链技术快速发展，保持学习

### 推荐资源：
- 📚 [Solidity 官方文档](https://docs.soliditylang.org/)
- 🛡️ [OpenZeppelin 合约库](https://docs.openzeppelin.com/)
- 🎯 [Ethernaut 挑战](https://ethernaut.openzeppelin.com/)
- 💬 [以太坊开发者社区](https://ethereum.org/en/community/)

**祝你在 Web3 开发之路上越走越远！** 🚀

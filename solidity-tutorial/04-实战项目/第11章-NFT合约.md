# 第11章：NFT (ERC721) 合约

本章学习如何创建 NFT（非同质化代币）合约，实现数字藏品、游戏道具等应用。

## 11.1 ERC721 标准简介

ERC721 是非同质化代币标准，每个代币都是独一无二的。

### ERC20 vs ERC721
```
┌──────────────────────────────────────────────────┐
│ 特性      │ ERC20             │ ERC721          │
├──────────────────────────────────────────────────┤
│ 可替代性  │ 同质化（可替代）  │ 非同质化（唯一）│
│ 单位      │ 可分割            │ 不可分割        │
│ 标识      │ 余额数量          │ 唯一 tokenId    │
│ 应用      │ 货币、积分        │ 艺术品、地产    │
└──────────────────────────────────────────────────┘
```

### 核心接口
```solidity
interface IERC721 {
    event Transfer(address indexed from, address indexed to, uint256 indexed tokenId);
    event Approval(address indexed owner, address indexed approved, uint256 indexed tokenId);
    event ApprovalForAll(address indexed owner, address indexed operator, bool approved);

    function balanceOf(address owner) external view returns (uint256);
    function ownerOf(uint256 tokenId) external view returns (address);
    function safeTransferFrom(address from, address to, uint256 tokenId) external;
    function transferFrom(address from, address to, uint256 tokenId) external;
    function approve(address to, uint256 tokenId) external;
    function getApproved(uint256 tokenId) external view returns (address);
    function setApprovalForAll(address operator, bool approved) external;
    function isApprovedForAll(address owner, address operator) external view returns (bool);
}
```

## 11.2 基础 NFT 实现

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract BasicNFT {
    string public name;
    string public symbol;
    uint256 private _tokenIdCounter;

    // tokenId → owner
    mapping(uint256 => address) private _owners;

    // owner → token count
    mapping(address => uint256) private _balances;

    // tokenId → approved address
    mapping(uint256 => address) private _tokenApprovals;

    // owner → operator → approved
    mapping(address => mapping(address => bool)) private _operatorApprovals;

    event Transfer(address indexed from, address indexed to, uint256 indexed tokenId);
    event Approval(address indexed owner, address indexed approved, uint256 indexed tokenId);
    event ApprovalForAll(address indexed owner, address indexed operator, bool approved);

    constructor(string memory _name, string memory _symbol) {
        name = _name;
        symbol = _symbol;
    }

    // 查询余额
    function balanceOf(address owner) public view returns (uint256) {
        require(owner != address(0), "Query for zero address");
        return _balances[owner];
    }

    // 查询所有者
    function ownerOf(uint256 tokenId) public view returns (address) {
        address owner = _owners[tokenId];
        require(owner != address(0), "Token does not exist");
        return owner;
    }

    // 转账
    function transferFrom(address from, address to, uint256 tokenId) public {
        require(_isApprovedOrOwner(msg.sender, tokenId), "Not approved");
        _transfer(from, to, tokenId);
    }

    // 授权单个 token
    function approve(address to, uint256 tokenId) public {
        address owner = ownerOf(tokenId);
        require(msg.sender == owner || isApprovedForAll(owner, msg.sender),
            "Not authorized");

        _tokenApprovals[tokenId] = to;
        emit Approval(owner, to, tokenId);
    }

    // 查询授权
    function getApproved(uint256 tokenId) public view returns (address) {
        require(_owners[tokenId] != address(0), "Token does not exist");
        return _tokenApprovals[tokenId];
    }

    // 授权所有 token
    function setApprovalForAll(address operator, bool approved) public {
        require(operator != msg.sender, "Cannot approve self");
        _operatorApprovals[msg.sender][operator] = approved;
        emit ApprovalForAll(msg.sender, operator, approved);
    }

    // 查询是否授权所有
    function isApprovedForAll(address owner, address operator)
        public
        view
        returns (bool)
    {
        return _operatorApprovals[owner][operator];
    }

    // 铸造 NFT
    function mint(address to) public returns (uint256) {
        uint256 tokenId = _tokenIdCounter++;
        _mint(to, tokenId);
        return tokenId;
    }

    // 内部函数
    function _transfer(address from, address to, uint256 tokenId) internal {
        require(ownerOf(tokenId) == from, "From is not owner");
        require(to != address(0), "Transfer to zero address");

        // 清除授权
        _tokenApprovals[tokenId] = address(0);

        _balances[from] -= 1;
        _balances[to] += 1;
        _owners[tokenId] = to;

        emit Transfer(from, to, tokenId);
    }

    function _mint(address to, uint256 tokenId) internal {
        require(to != address(0), "Mint to zero address");
        require(_owners[tokenId] == address(0), "Token already minted");

        _balances[to] += 1;
        _owners[tokenId] = to;

        emit Transfer(address(0), to, tokenId);
    }

    function _isApprovedOrOwner(address spender, uint256 tokenId)
        internal
        view
        returns (bool)
    {
        address owner = ownerOf(tokenId);
        return (spender == owner ||
                getApproved(tokenId) == spender ||
                isApprovedForAll(owner, spender));
    }
}
```

## 11.3 带元数据的 NFT

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract NFTWithMetadata is BasicNFT {
    // tokenId → URI
    mapping(uint256 => string) private _tokenURIs;

    string private _baseURIextended;

    constructor(string memory _name, string memory _symbol, string memory baseURI)
        BasicNFT(_name, _symbol)
    {
        _baseURIextended = baseURI;
    }

    // 设置基础 URI
    function setBaseURI(string memory baseURI) public {
        _baseURIextended = baseURI;
    }

    // 获取 token URI
    function tokenURI(uint256 tokenId) public view returns (string memory) {
        require(_owners[tokenId] != address(0), "Token does not exist");

        string memory _tokenURI = _tokenURIs[tokenId];

        // 如果有自定义 URI，返回自定义 URI
        if (bytes(_tokenURI).length > 0) {
            return _tokenURI;
        }

        // 否则返回 baseURI + tokenId
        return string(abi.encodePacked(_baseURIextended, toString(tokenId)));
    }

    // 设置 token URI
    function setTokenURI(uint256 tokenId, string memory _tokenURI) public {
        require(_owners[tokenId] == msg.sender, "Not owner");
        _tokenURIs[tokenId] = _tokenURI;
    }

    // 铸造并设置 URI
    function mintWithURI(address to, string memory uri) public returns (uint256) {
        uint256 tokenId = mint(to);
        _tokenURIs[tokenId] = uri;
        return tokenId;
    }

    // uint to string 辅助函数
    function toString(uint256 value) internal pure returns (string memory) {
        if (value == 0) {
            return "0";
        }
        uint256 temp = value;
        uint256 digits;
        while (temp != 0) {
            digits++;
            temp /= 10;
        }
        bytes memory buffer = new bytes(digits);
        while (value != 0) {
            digits -= 1;
            buffer[digits] = bytes1(uint8(48 + uint256(value % 10)));
            value /= 10;
        }
        return string(buffer);
    }
}
```

## 11.4 完整的 NFT 市场合约

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract NFTMarketplace {
    struct NFT {
        uint256 tokenId;
        address owner;
        string uri;
        uint256 price;
        bool forSale;
    }

    string public name = "MyNFT";
    string public symbol = "MNFT";
    uint256 private _tokenIdCounter;
    address public contractOwner;

    mapping(uint256 => NFT) public nfts;
    mapping(address => uint256[]) public ownerTokens;

    event Minted(uint256 indexed tokenId, address indexed owner, string uri);
    event Listed(uint256 indexed tokenId, uint256 price);
    event Unlisted(uint256 indexed tokenId);
    event Sold(uint256 indexed tokenId, address indexed from, address indexed to, uint256 price);
    event Transfer(address indexed from, address indexed to, uint256 indexed tokenId);

    modifier onlyTokenOwner(uint256 tokenId) {
        require(nfts[tokenId].owner == msg.sender, "Not token owner");
        _;
    }

    modifier tokenExists(uint256 tokenId) {
        require(nfts[tokenId].owner != address(0), "Token does not exist");
        _;
    }

    constructor() {
        contractOwner = msg.sender;
    }

    // 铸造 NFT
    function mint(string memory uri) public returns (uint256) {
        uint256 tokenId = _tokenIdCounter++;

        nfts[tokenId] = NFT({
            tokenId: tokenId,
            owner: msg.sender,
            uri: uri,
            price: 0,
            forSale: false
        });

        ownerTokens[msg.sender].push(tokenId);

        emit Minted(tokenId, msg.sender, uri);
        emit Transfer(address(0), msg.sender, tokenId);

        return tokenId;
    }

    // 上架销售
    function listForSale(uint256 tokenId, uint256 price)
        public
        onlyTokenOwner(tokenId)
    {
        require(price > 0, "Price must be greater than zero");

        nfts[tokenId].price = price;
        nfts[tokenId].forSale = true;

        emit Listed(tokenId, price);
    }

    // 下架
    function unlist(uint256 tokenId) public onlyTokenOwner(tokenId) {
        nfts[tokenId].forSale = false;
        nfts[tokenId].price = 0;

        emit Unlisted(tokenId);
    }

    // 购买 NFT
    function buy(uint256 tokenId) public payable tokenExists(tokenId) {
        NFT storage nft = nfts[tokenId];

        require(nft.forSale, "NFT not for sale");
        require(msg.value >= nft.price, "Insufficient payment");
        require(msg.sender != nft.owner, "Cannot buy your own NFT");

        address previousOwner = nft.owner;
        uint256 price = nft.price;

        // 转移所有权
        nft.owner = msg.sender;
        nft.forSale = false;
        nft.price = 0;

        // 更新所有者列表
        _removeTokenFromOwner(previousOwner, tokenId);
        ownerTokens[msg.sender].push(tokenId);

        // 转账给卖家
        payable(previousOwner).transfer(price);

        // 退还多余的 ETH
        if (msg.value > price) {
            payable(msg.sender).transfer(msg.value - price);
        }

        emit Sold(tokenId, previousOwner, msg.sender, price);
        emit Transfer(previousOwner, msg.sender, tokenId);
    }

    // 转移 NFT
    function transfer(address to, uint256 tokenId)
        public
        onlyTokenOwner(tokenId)
    {
        require(to != address(0), "Transfer to zero address");
        require(!nfts[tokenId].forSale, "Cannot transfer NFT for sale");

        address from = msg.sender;

        nfts[tokenId].owner = to;

        _removeTokenFromOwner(from, tokenId);
        ownerTokens[to].push(tokenId);

        emit Transfer(from, to, tokenId);
    }

    // 销毁 NFT
    function burn(uint256 tokenId) public onlyTokenOwner(tokenId) {
        require(!nfts[tokenId].forSale, "Cannot burn NFT for sale");

        address owner = nfts[tokenId].owner;
        delete nfts[tokenId];

        _removeTokenFromOwner(owner, tokenId);

        emit Transfer(owner, address(0), tokenId);
    }

    // 查询函数
    function tokenURI(uint256 tokenId)
        public
        view
        tokenExists(tokenId)
        returns (string memory)
    {
        return nfts[tokenId].uri;
    }

    function ownerOf(uint256 tokenId)
        public
        view
        tokenExists(tokenId)
        returns (address)
    {
        return nfts[tokenId].owner;
    }

    function balanceOf(address owner) public view returns (uint256) {
        return ownerTokens[owner].length;
    }

    function getOwnerTokens(address owner)
        public
        view
        returns (uint256[] memory)
    {
        return ownerTokens[owner];
    }

    function getAllNFTsForSale() public view returns (NFT[] memory) {
        uint256 count = 0;

        // 计算在售 NFT 数量
        for (uint256 i = 0; i < _tokenIdCounter; i++) {
            if (nfts[i].forSale && nfts[i].owner != address(0)) {
                count++;
            }
        }

        // 创建数组并填充
        NFT[] memory forSale = new NFT[](count);
        uint256 index = 0;

        for (uint256 i = 0; i < _tokenIdCounter; i++) {
            if (nfts[i].forSale && nfts[i].owner != address(0)) {
                forSale[index] = nfts[i];
                index++;
            }
        }

        return forSale;
    }

    // 内部函数
    function _removeTokenFromOwner(address owner, uint256 tokenId) private {
        uint256[] storage tokens = ownerTokens[owner];
        for (uint256 i = 0; i < tokens.length; i++) {
            if (tokens[i] == tokenId) {
                tokens[i] = tokens[tokens.length - 1];
                tokens.pop();
                break;
            }
        }
    }
}
```

## 11.5 元数据标准

### ERC721 元数据 JSON 格式
```json
{
    "name": "My NFT #1",
    "description": "This is my first NFT",
    "image": "ipfs://QmXxx.../image.png",
    "attributes": [
        {
            "trait_type": "Background",
            "value": "Blue"
        },
        {
            "trait_type": "Rarity",
            "value": "Common"
        },
        {
            "trait_type": "Power",
            "value": 100,
            "display_type": "number"
        }
    ]
}
```

### 存储元数据的方式
1. **IPFS**（推荐）：去中心化存储
   ```
   ipfs://QmXxx.../metadata.json
   ```

2. **中心化服务器**：
   ```
   https://api.myproject.com/nft/1
   ```

3. **链上存储**（昂贵）：
   ```solidity
   string memory metadata = "data:application/json;base64,...";
   ```

## 11.6 实战示例：数字艺术 NFT

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract DigitalArtNFT {
    struct Artwork {
        string name;
        string artist;
        string ipfsHash;
        uint256 creationDate;
        uint256 royaltyPercentage;  // 版税百分比（0-100）
    }

    mapping(uint256 => Artwork) public artworks;
    mapping(uint256 => address) public tokenOwner;
    mapping(uint256 => address) public tokenCreator;  // 原创作者

    uint256 private _nextTokenId;

    event ArtworkMinted(
        uint256 indexed tokenId,
        address indexed creator,
        string name,
        string ipfsHash
    );

    event ArtworkSold(
        uint256 indexed tokenId,
        address indexed from,
        address indexed to,
        uint256 price,
        uint256 royalty
    );

    // 铸造艺术品 NFT
    function mintArtwork(
        string memory name,
        string memory artist,
        string memory ipfsHash,
        uint256 royaltyPercentage
    ) public returns (uint256) {
        require(royaltyPercentage <= 100, "Royalty too high");

        uint256 tokenId = _nextTokenId++;

        artworks[tokenId] = Artwork({
            name: name,
            artist: artist,
            ipfsHash: ipfsHash,
            creationDate: block.timestamp,
            royaltyPercentage: royaltyPercentage
        });

        tokenOwner[tokenId] = msg.sender;
        tokenCreator[tokenId] = msg.sender;

        emit ArtworkMinted(tokenId, msg.sender, name, ipfsHash);

        return tokenId;
    }

    // 出售艺术品（自动支付版税）
    function sellArtwork(uint256 tokenId, address buyer) public payable {
        require(tokenOwner[tokenId] == msg.sender, "Not owner");
        require(buyer != address(0), "Invalid buyer");

        uint256 price = msg.value;
        uint256 royalty = (price * artworks[tokenId].royaltyPercentage) / 100;
        uint256 sellerProceeds = price - royalty;

        address creator = tokenCreator[tokenId];
        address seller = msg.sender;

        // 转移所有权
        tokenOwner[tokenId] = buyer;

        // 支付版税给原创作者
        if (royalty > 0 && creator != seller) {
            payable(creator).transfer(royalty);
        }

        // 支付给卖家
        payable(seller).transfer(sellerProceeds);

        emit ArtworkSold(tokenId, seller, buyer, price, royalty);
    }

    // 获取艺术品信息
    function getArtworkInfo(uint256 tokenId)
        public
        view
        returns (
            string memory name,
            string memory artist,
            string memory ipfsHash,
            uint256 creationDate,
            address owner,
            address creator
        )
    {
        Artwork memory artwork = artworks[tokenId];
        return (
            artwork.name,
            artwork.artist,
            artwork.ipfsHash,
            artwork.creationDate,
            tokenOwner[tokenId],
            tokenCreator[tokenId]
        );
    }
}
```

## 📝 实践任务

### 任务 1：简单 NFT 铸造
创建一个 NFT 合约，实现：
- 铸造 NFT
- 转移 NFT
- 查询所有者和余额
- 每个 NFT 有唯一的元数据 URI

### 任务 2：NFT 盲盒
实现一个盲盒 NFT：
- 用户购买盲盒
- 随机揭晓 NFT 属性
- 不同稀有度的 NFT
- 限量发售

### 任务 3：NFT 租赁市场
创建 NFT 租赁功能：
- NFT 持有者可以出租
- 租客可以在租期内使用
- 自动到期归还
- 租金自动分配

## 📝 本章小结

- ✅ 理解 ERC721 标准
- ✅ 实现基础 NFT 合约
- ✅ 添加元数据功能
- ✅ 创建 NFT 市场
- ✅ 实现版税机制

## 🎯 最佳实践

1. **使用 IPFS 存储元数据**：去中心化且永久
2. **实现版税机制**：保护创作者权益
3. **SafeTransfer**：检查接收方能否接收 NFT
4. **清晰的所有权记录**：准确维护所有者列表
5. **Gas 优化**：批量操作时注意循环

## 下一章

[第12章：DeFi 应用开发](./第12章-DeFi应用开发.md) 将学习如何开发去中心化金融应用。

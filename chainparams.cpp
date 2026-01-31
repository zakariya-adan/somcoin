// Copyright (c) 2010 Satoshi Nakamoto
// Copyright (c) 2009-present The SomCoin Core developers
// Distributed under the MIT software license.

#include <kernel/chainparams.h>

#include <chainparamsseeds.h>
#include <consensus/amount.h>
#include <consensus/merkle.h>
#include <consensus/params.h>
#include <crypto/hex_base.h>
#include <hash.h>
#include <kernel/messagestartchars.h>
#include <primitives/block.h>
#include <primitives/transaction.h>
#include <script/script.h>
#include <uint256.h>
#include <util/chaintype.h>

#include <algorithm>
#include <cassert>
#include <cstring>

using namespace util::hex_literals;

/* ======================= GENESIS ======================= */

static CBlock CreateGenesisBlock(
    const char* pszTimestamp,
    const CScript& genesisOutputScript,
    uint32_t nTime,
    uint32_t nNonce,
    uint32_t nBits,
    int32_t nVersion,
    const CAmount& genesisReward)
{
    CMutableTransaction txNew;
    txNew.version = 1;
    txNew.vin.resize(1);
    txNew.vout.resize(1);

    txNew.vin[0].scriptSig =
        CScript() << 486604799 << CScriptNum(4)
                  << std::vector<unsigned char>(
                         (const unsigned char*)pszTimestamp,
                         (const unsigned char*)pszTimestamp + strlen(pszTimestamp));

    txNew.vout[0].nValue = genesisReward;
    txNew.vout[0].scriptPubKey = genesisOutputScript;

    CBlock genesis;
    genesis.nTime = nTime;
    genesis.nBits = nBits;
    genesis.nNonce = nNonce;
    genesis.nVersion = nVersion;
    genesis.vtx.push_back(MakeTransactionRef(std::move(txNew)));
    genesis.hashPrevBlock.SetNull();
    genesis.hashMerkleRoot = BlockMerkleRoot(genesis);

    return genesis;
}

static CBlock CreateGenesisBlock(
    uint32_t nTime,
    uint32_t nNonce,
    uint32_t nBits,
    int32_t nVersion,
    const CAmount& genesisReward)
{
    const char* pszTimestamp =
        "SomCoin genesis block created by Zakariya Adan in 2026";

    const CScript genesisOutputScript =
        CScript() << "04678afdb0fe5548271967f1a67130b7105cd6a828e03909a67962e0ea1f61deb"
                     "649f6bc3f4cef38c4f35504e51ec112de5c384df7ba0b8d578a4c702b6bf11d5f"_hex
                  << OP_CHECKSIG;

    return CreateGenesisBlock(
        pszTimestamp,
        genesisOutputScript,
        nTime,
        nNonce,
        nBits,
        nVersion,
        genesisReward);
}

/* ======================= MAIN ======================= */

class CMainParams : public CChainParams
{
public:
    CMainParams()
    {
        m_chain_type = ChainType::MAIN;

        consensus.nSubsidyHalvingInterval = 210000;
        consensus.BIP34Height = 1;
        consensus.BIP65Height = 1;
        consensus.BIP66Height = 1;
        consensus.CSVHeight = 1;
        consensus.SegwitHeight = 1;

        consensus.powLimit =
            uint256{"00000000ffffffffffffffffffffffffffffffffffffffffffffffffffffffff"};

        consensus.nPowTargetTimespan = 14 * 24 * 60 * 60;
        consensus.nPowTargetSpacing = 10 * 60;

        consensus.fPowAllowMinDifficultyBlocks = false;
        consensus.fPowNoRetargeting = false;

        pchMessageStart[0] = 0x73;
        pchMessageStart[1] = 0x6f;
        pchMessageStart[2] = 0x6d;
        pchMessageStart[3] = 0x63;

        nDefaultPort = 40444;
        nPruneAfterHeight = 100000;

        genesis = CreateGenesisBlock(
            1769532133,
            3860,
            0x1e0ffff0,
            1,
            100 * COIN);

        consensus.hashGenesisBlock = genesis.GetHash();

        vSeeds.clear();
        vFixedSeeds.clear();

        base58Prefixes[PUBKEY_ADDRESS] = {0};
        base58Prefixes[SCRIPT_ADDRESS] = {5};
        base58Prefixes[SECRET_KEY] = {128};

        bech32_hrp = "som";
    }
};

/* ======================= TESTNET ======================= */

class CTestNetParams : public CChainParams
{
public:
    CTestNetParams()
    {
        m_chain_type = ChainType::TESTNET;

        consensus.fPowAllowMinDifficultyBlocks = true;

        pchMessageStart[0] = 0x74;
        pchMessageStart[1] = 0x73;
        pchMessageStart[2] = 0x6f;
        pchMessageStart[3] = 0x6d;

        nDefaultPort = 40445;

        genesis = CreateGenesisBlock(
            1769532133,
            999,
            0x1e0ffff0,
            1,
            100 * COIN);

        consensus.hashGenesisBlock = genesis.GetHash();

        base58Prefixes[PUBKEY_ADDRESS] = {111};
        base58Prefixes[SCRIPT_ADDRESS] = {196};
        base58Prefixes[SECRET_KEY] = {239};

        bech32_hrp = "tsom";
    }
};

/* ======================= TESTNET4 ======================= */

class CTestNet4Params : public CChainParams
{
public:
    CTestNet4Params()
    {
        m_chain_type = ChainType::TESTNET4;

        pchMessageStart[0] = 0x74;
        pchMessageStart[1] = 0x34;
        pchMessageStart[2] = 0x73;
        pchMessageStart[3] = 0x6d;

        nDefaultPort = 40446;

        genesis = CreateGenesisBlock(
            1769532133,
            1500,
            0x1e0ffff0,
            1,
            100 * COIN);

        consensus.hashGenesisBlock = genesis.GetHash();

        base58Prefixes[PUBKEY_ADDRESS] = {111};
        base58Prefixes[SCRIPT_ADDRESS] = {196};
        base58Prefixes[SECRET_KEY] = {239};

        bech32_hrp = "t4som";
    }
};

/* ======================= FACTORY ======================= */

std::unique_ptr<const CChainParams> CChainParams::Main()
{
    return std::make_unique<const CMainParams>();
}

std::unique_ptr<const CChainParams> CChainParams::TestNet()
{
    return std::make_unique<const CTestNetParams>();
}

std::unique_ptr<const CChainParams> CChainParams::TestNet4()
{
    return std::make_unique<const CTestNet4Params>();
}

// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract PredictionLedger {
    struct Anchor {
        uint256 index;
        string timestamp;
        string source;
        bytes32 offchainRecordId;
        bytes32 payloadHash;
        bytes32 previousHash;
        bytes32 anchorHash;
        bytes signature;
        address writer;
        string storageMode;
    }

    Anchor[] private anchors;

    event AnchorAppended(
        uint256 indexed index,
        bytes32 indexed offchainRecordId,
        bytes32 payloadHash,
        bytes32 anchorHash,
        address writer
    );

    function appendAnchor(
        string calldata timestamp,
        string calldata source,
        bytes32 offchainRecordId,
        bytes32 payloadHash,
        bytes32 previousHash,
        bytes32 anchorHash,
        bytes calldata signature,
        string calldata storageMode
    ) external returns (uint256) {
        uint256 index = anchors.length;
        anchors.push(
            Anchor({
                index: index,
                timestamp: timestamp,
                source: source,
                offchainRecordId: offchainRecordId,
                payloadHash: payloadHash,
                previousHash: previousHash,
                anchorHash: anchorHash,
                signature: signature,
                writer: msg.sender,
                storageMode: storageMode
            })
        );

        emit AnchorAppended(index, offchainRecordId, payloadHash, anchorHash, msg.sender);
        return index;
    }

    function anchorCount() external view returns (uint256) {
        return anchors.length;
    }

    function getAnchor(
        uint256 index
    )
        external
        view
        returns (
            uint256,
            string memory,
            string memory,
            bytes32,
            bytes32,
            bytes32,
            bytes32,
            bytes memory,
            address,
            string memory
        )
    {
        Anchor storage anchor = anchors[index];
        return (
            anchor.index,
            anchor.timestamp,
            anchor.source,
            anchor.offchainRecordId,
            anchor.payloadHash,
            anchor.previousHash,
            anchor.anchorHash,
            anchor.signature,
            anchor.writer,
            anchor.storageMode
        );
    }
}

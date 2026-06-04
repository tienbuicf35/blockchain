package main

import (
	"encoding/json"
	"fmt"
	"strconv"

	"github.com/hyperledger/fabric-contract-api-go/contractapi"
)

type PredictionLedgerContract struct {
	contractapi.Contract
}

type PredictionAnchor struct {
	Index            int    `json:"index"`
	Timestamp        string `json:"timestamp"`
	Source           string `json:"source"`
	OffchainRecordID string `json:"offchain_record_id"`
	PayloadHash      string `json:"payload_hash"`
	PreviousHash     string `json:"previous_hash"`
	Hash             string `json:"hash"`
	Signature        string `json:"signature"`
	Storage          string `json:"storage"`
	WriterMSP        string `json:"writer_msp"`
	TxID             string `json:"tx_id"`
}

func anchorKey(index int) string {
	return fmt.Sprintf("prediction-anchor:%020d", index)
}

func (c *PredictionLedgerContract) RecordPredictionAnchor(
	ctx contractapi.TransactionContextInterface,
	indexText string,
	timestamp string,
	source string,
	offchainRecordID string,
	payloadHash string,
	previousHash string,
	hash string,
	signature string,
	storage string,
) error {
	index, err := strconv.Atoi(indexText)
	if err != nil {
		return fmt.Errorf("invalid index %q: %w", indexText, err)
	}
	if hash == "" || payloadHash == "" || offchainRecordID == "" {
		return fmt.Errorf("hash, payloadHash, and offchainRecordID are required")
	}

	key := anchorKey(index)
	existing, err := ctx.GetStub().GetState(key)
	if err != nil {
		return err
	}
	if existing != nil {
		return fmt.Errorf("anchor already exists at index %d", index)
	}

	mspID, _ := ctx.GetClientIdentity().GetMSPID()
	anchor := PredictionAnchor{
		Index:            index,
		Timestamp:        timestamp,
		Source:           source,
		OffchainRecordID: offchainRecordID,
		PayloadHash:      payloadHash,
		PreviousHash:     previousHash,
		Hash:             hash,
		Signature:        signature,
		Storage:          storage,
		WriterMSP:        mspID,
		TxID:             ctx.GetStub().GetTxID(),
	}

	payload, err := json.Marshal(anchor)
	if err != nil {
		return err
	}
	if err := ctx.GetStub().PutState(key, payload); err != nil {
		return err
	}
	return ctx.GetStub().PutState("prediction-anchor:head", payload)
}

func (c *PredictionLedgerContract) GetPredictionAnchor(ctx contractapi.TransactionContextInterface, indexText string) (*PredictionAnchor, error) {
	index, err := strconv.Atoi(indexText)
	if err != nil {
		return nil, fmt.Errorf("invalid index %q: %w", indexText, err)
	}
	payload, err := ctx.GetStub().GetState(anchorKey(index))
	if err != nil {
		return nil, err
	}
	if payload == nil {
		return nil, fmt.Errorf("anchor %d not found", index)
	}

	var anchor PredictionAnchor
	if err := json.Unmarshal(payload, &anchor); err != nil {
		return nil, err
	}
	return &anchor, nil
}

func (c *PredictionLedgerContract) GetHead(ctx contractapi.TransactionContextInterface) (*PredictionAnchor, error) {
	payload, err := ctx.GetStub().GetState("prediction-anchor:head")
	if err != nil {
		return nil, err
	}
	if payload == nil {
		return nil, fmt.Errorf("ledger is empty")
	}

	var anchor PredictionAnchor
	if err := json.Unmarshal(payload, &anchor); err != nil {
		return nil, err
	}
	return &anchor, nil
}

func main() {
	chaincode, err := contractapi.NewChaincode(&PredictionLedgerContract{})
	if err != nil {
		panic(err)
	}
	if err := chaincode.Start(); err != nil {
		panic(err)
	}
}

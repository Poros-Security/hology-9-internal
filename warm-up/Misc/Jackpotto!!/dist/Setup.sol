// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "./TimeVariantCasino.sol";

contract Setup {
    TimeVariantCasino public casino;

    event TargetDeployed(address targetAddress);

    constructor() payable {
        bytes32 previousBlockHash =
            block.number == 0 ? bytes32(0) : blockhash(block.number - 1);

        uint256 initialSeed = uint256(
            keccak256(
                abi.encodePacked(
                    previousBlockHash,
                    block.coinbase,
                    msg.sender
                )
            )
        );

        casino = new TimeVariantCasino(initialSeed);

        emit TargetDeployed(address(casino));
    }

    function isSolved() external view returns (bool) {
        return casino.isSolved();
    }
}

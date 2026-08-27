// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract TimeVariantCasino {
    uint256 public constant P =
        0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F;

    uint256 public constant A = 0x514C4F4E474D55534B;
    uint256 public constant C = 0x1337BEEF;

    uint256 private state;
    bool public isSolved;

    event Spin(address indexed player, uint80 partialState, uint256 timestamp);

    constructor(uint256 _seed) {
        state =
            uint256(keccak256(abi.encodePacked(_seed, block.timestamp))) %
            P;
    }

    function spin() external returns (uint80) {
        uint256 t = block.timestamp;

        uint256 nextState = mulmod(A, state, P);
        nextState = addmod(nextState, C, P);
        nextState = addmod(nextState, t, P);

        state = nextState;

        uint80 output = uint80(state >> 176);

        emit Spin(msg.sender, output, t);
        return output;
    }

    function exploit(uint256 exactNextState) external {
        uint256 t = block.timestamp;

        uint256 expectedNext = mulmod(A, state, P);
        expectedNext = addmod(expectedNext, C, P);
        expectedNext = addmod(expectedNext, t, P);

        require(exactNextState == expectedNext, "No jackpot :(");

        state = expectedNext;
        isSolved = true;
    }
}

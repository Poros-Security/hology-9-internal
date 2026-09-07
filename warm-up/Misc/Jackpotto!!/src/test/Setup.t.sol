// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "../contracts/Setup.sol";

interface Vm {
    function roll(uint256 newHeight) external;
}

contract SetupGenesisBlockTest {
    Vm private constant vm = Vm(address(uint160(uint256(keccak256("hevm cheat code")))));

    function testDeploysAtGenesisBlock() external {
        vm.roll(0);
        new Setup();
    }
}
# Logis Vision AGV_Control

## 프로젝트 개요

![Logis_Vision_Logo](https://raw.githubusercontent.com/LogisVision/Logis_Platform/refs/heads/master/Basic%20Theme%403x.png)

**"Logis Vision"** 은 두 대의 AGV(Jetson Nano)를 이용한 통합 물류 관리 솔루션으로,
입고된 상품을 자동으로 등록하고 관리자 지정 위치로 이동시킵니다.

**"Logis Vision AGV Control"** 은 Demon Server와 통신하며 Work List에 쌓여있는 작업을 수행합니다.

- AGV Team 1 : AGV Team2가 운반해놓은 물품을 Road Following을 통해 주행하고 특정 선반에 올려두는 작업을 수행합니다.
- AGV Team 2 : 새로 입고되는 물품에 대해서 Road Following을 통해 AGV Team 1이 운반할 수 있도록 작업대에 적재합니다.

## 기능

- Road Following
- Recognize Working Area
- Carrying Boxes
- Communication with Server
- Remote Control by QT Controller

## 진행 상황

### Team 1

- Collect Road Image
- Train Road Following Model

### Team2

## 해야할 것

### Team 1

- Road Following Test
- Recognize Working Area
- Carrying Boxes
- Communication with Server

### Team2

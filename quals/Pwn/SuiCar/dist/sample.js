let samples = [13.37, 42.0, 86.4];
let frame = SuiTele.makeFrame(samples);

print("kind before = " + SuiArray.kind(samples));

SuiDash.render(() => {
  print("dashboard callback ok");
});

SuiTele.calibrate(frame, () => {
  print("calibration callback");
});

print("kind after = " + SuiArray.kind(samples));
print(SuiTele.exportFrame(frame));


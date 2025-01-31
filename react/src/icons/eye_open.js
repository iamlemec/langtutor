let upperLine = SymPath({
  fy: x => 0.3 * sin(pi * x) + 0.5,
  xlim: [0.1, 0.9], N: 50,
});
let lowerLine = SymPath({
  fy: x => 0.5 - 0.3 * sin(pi * x),
  xlim: [0.1, 0.9], N: 50,
});
let pupil = Circle({pos: [0.5, 0.5], rad: 0.06, fill: 'black'});
let eyeIcon = Group([upperLine, lowerLine, pupil]);
return SVG(eyeIcon, {size: 25, aspect: 1, stroke_width: 2});

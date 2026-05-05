const modelData = {
  '0-800': {
    coef: [-0.08042425269324323, 0.009116274821439584, 0.07130797787196914],
    intercept: [0.8927665823295349, -1.7946778153978862, 0.9019112330698089],
  },
  '800-1000': {
    coef: [-0.08057697448490471, -0.0060100056454605675, 0.08658698013037397],
    intercept: [0.8859735251010523, -1.76086825754242, 0.8748947324384938],
  },
  '1000-1200': {
    coef: [-0.0939904630964961, -7.280695958535588e-05, 0.09406327005600078],
    intercept: [0.8690876337718922, -1.7303258788890576, 0.8612382451279308],
  },
  '1200-1400': {
    coef: [-0.10303771784267027, -0.0050934219202124105, 0.10813113976308622],
    intercept: [0.8207577312222352, -1.637455113763792, 0.8166973825629076],
  },
  '1400-1600': {
    coef: [-0.1144779687382134, -0.0059605627876129705, 0.12043853152538406],
    intercept: [0.7824740354180753, -1.559541770587369, 0.7770677351727048],
  },
  '1600-1800': {
    coef: [-0.12394858847381096, -0.0034471827497344907, 0.12739577122355328],
    intercept: [0.7148606015457459, -1.4272487601128003, 0.7123881585713069],
  },
  '1800-2000': {
    coef: [-0.1329526534012561, -0.0059663685602618305, 0.13891902196158737],
    intercept: [0.6578407912105022, -1.310551511840741, 0.6527107206357613],
  },
  '2000-2200': {
    coef: [-0.1483936136997544, -0.003091580220318653, 0.15148519392012835],
    intercept: [0.5994923898948976, -1.2067101380283725, 0.6072177481485024],
  },
  '2200-3000': {
    coef: [-0.1597756549019772, -0.002092102621922702, 0.16186775752454718],
    intercept: [0.48676269293024177, -0.9845510870716739, 0.49778839410777254],
  },
};

const select = document.getElementById('eloRange');
const evalInput = document.getElementById('evalInput');
const predictButton = document.getElementById('predictButton');
const winOutput = document.getElementById('winProb');
const drawOutput = document.getElementById('drawProb');
const lossOutput = document.getElementById('lossProb');

const sideInputs = document.querySelectorAll('input[name="color"]');

function softmax(scores) {
  const maxScore = Math.max(...scores);
  const exps = scores.map((value) => Math.exp(value - maxScore));
  const sum = exps.reduce((total, value) => total + value, 0);
  return exps.map((value) => value / sum);
}

function predict(evalValue, eloKey, color) {
  const model = modelData[eloKey];
  const rawScores = model.coef.map((coef, index) => coef * evalValue + model.intercept[index]);
  const probs = softmax(rawScores);

  let winProb = probs[2];
  let drawProb = probs[1];
  let lossProb = probs[0];

  if (color === 'black') {
    const blackWin = lossProb;
    lossProb = winProb;
    winProb = blackWin;
  }

  return { winProb, drawProb, lossProb };
}

function formatPct(value) {
  return `${(value * 100).toFixed(1)}%`;
}

function updateResults() {
  const eloKey = select.value;
  const evalValue = Number(evalInput.value) || 0;
  const color = document.querySelector('input[name="color"]:checked').value;
  const { winProb, drawProb, lossProb } = predict(evalValue, eloKey, color);

  winOutput.textContent = formatPct(winProb);
  drawOutput.textContent = formatPct(drawProb);
  lossOutput.textContent = formatPct(lossProb);
}

function init() {
  Object.keys(modelData).forEach((key) => {
    const option = document.createElement('option');
    option.value = key;
    option.textContent = key;
    select.appendChild(option);
  });

  predictButton.addEventListener('click', updateResults);
  updateResults();
}

init();
